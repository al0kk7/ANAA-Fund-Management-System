from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Event(models.Model):
    """
    Something ANAA is raising/spending money for -- e.g. "2026 Annual
    Reunion", "Scholarship Program 2026". A Budget is created against
    one Event.

    is_closed marks an event as finished and reported on -- the
    "Settled"/"Audited" end of the project workflow diagram. A closed
    event is a historical record: its budgets/allocations/requests
    remain visible but the event is flagged done for reporting.
    """
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    event_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="events_closed"
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def total_budgeted(self):
        return self.budgets.aggregate(total=models.Sum("total_amount"))["total"] or Decimal("0.00")

    def total_spent(self):
        from requests_app.models import ExpenseRequest
        return ExpenseRequest.objects.filter(
            allocation__budget__event=self,
            status=ExpenseRequest.STATUS_PAID,
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    def total_leftover(self):
        return self.total_budgeted() - self.total_spent()

    def total_actual_expenses(self):
        """Sum of the real bills recorded after the event (EventExpense)."""
        return self.actual_expenses.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    def budget_variance(self):
        """
        Budgeted minus actual. Positive = came in under budget,
        negative = went over budget.
        """
        return self.total_budgeted() - self.total_actual_expenses()

    def expenses_missing_bills(self):
        """How many recorded expenses have no scanned bill attached yet."""
        return self.actual_expenses.filter(bill_file="").count()


class EventExpense(models.Model):
    """
    A real, after-the-fact expense for an Event -- one line per bill.

    Why this is separate from ExpenseRequest: an ExpenseRequest is the
    ESTIMATE stage (someone asks for money before the event, goes
    through verify/approve/pay). An EventExpense is the ACTUAL stage
    (after the event, someone records what was really spent, with the
    bill). The two will rarely match exactly, and the gap between
    them is exactly what the yearly audit is meant to show.

    Since the original bills are physical paper, bill_file holds a
    scan/photo, and physical_reference records WHERE the paper
    original is kept (e.g. "Blue folder, page 12") so an auditor can
    find it.
    """
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="actual_expenses")
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    paid_to = models.CharField(max_length=150, blank=True, help_text="Vendor / shop / person paid")
    bill_file = models.FileField(upload_to="expense_bills/%Y/%m/", blank=True)
    physical_reference = models.CharField(
        max_length=150, blank=True,
        help_text="Where the paper bill is filed, e.g. 'Blue folder, page 12'"
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="event_expenses_added"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expense_date", "created_at"]

    def __str__(self):
        return f"{self.description} - {self.amount} ({self.event.name})"

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")


class Budget(models.Model):
    """
    The total amount approved for an Event. Allocations are then
    carved out of this budget -- the sum of allocations must never
    exceed total_amount (enforced in Allocation.clean()).

    Budget itself is checked against actual Fund Receipts in
    clean() below: a Budget cannot commit more money than ANAA has
    actually received and not yet committed to another Budget. This
    is the same balance-validation pattern as Allocation.clean() and
    ExpenseRequest.transition_to(), applied one level higher --
    Fund Receipts -> Budgets -> Allocations -> Expense Requests each
    check against the level above them.
    """
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="budgets")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="budgets_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Budget for {self.event.name} - {self.total_amount}"

    def total_allocated(self):
        return self.allocations.aggregate(
            total=models.Sum("allocated_amount")
        )["total"] or Decimal("0.00")

    def remaining_balance(self):
        return self.total_amount - self.total_allocated()

    def clean(self):
        """
        Balance-validation algorithm, applied at the Fund -> Budget
        level: this budget's total_amount must not push the sum of
        all Budgets beyond total Fund Receipts actually recorded.
        """
        if self.total_amount is None:
            return

        # Imported here, not at module level, to avoid a circular
        # import (funds app has no dependency on budgets, so this is
        # safe either way, but keeping it local matches the deferred-
        # import style already used for cross-app totals elsewhere,
        # e.g. accounts/views.py).
        from funds.models import FundReceipt

        total_received = FundReceipt.objects.aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")

        existing_budgeted = Budget.objects.exclude(pk=self.pk).aggregate(
            total=models.Sum("total_amount")
        )["total"] or Decimal("0.00")

        prospective_total = existing_budgeted + self.total_amount

        if prospective_total > total_received:
            remaining = total_received - existing_budgeted
            raise ValidationError(
                f"This budget of {self.total_amount} exceeds the unallocated "
                f"funds on hand of {remaining} (total received: {total_received}, "
                f"already budgeted: {existing_budgeted})."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Allocation(models.Model):
    """
    A portion of a Budget set aside for a specific purpose (e.g.
    "Venue rental", "Catering"). ExpenseRequests (Iteration 4) will
    be submitted against a specific Allocation, not directly against
    a Budget.

    Core business rule: total allocated against a Budget can never
    exceed that Budget's total_amount. This is the balance-validation
    algorithm from the project's Analysis chapter.
    """
    budget = models.ForeignKey(Budget, on_delete=models.PROTECT, related_name="allocations")
    purpose = models.CharField(max_length=150)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="allocations_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.purpose} - {self.allocated_amount}"

    def total_approved_or_paid(self, exclude_request=None):
        """
        Sum of expense requests against this allocation that are
        already Approved or Paid -- i.e. money that is committed,
        not just requested. Used by ExpenseRequest.transition_to()
        to check a new approval doesn't overspend the allocation.
        Excludes exclude_request itself so re-checking an existing
        request being approved doesn't double count it.
        """
        qs = self.expense_requests.filter(status__in=["approved", "paid"])
        if exclude_request is not None and exclude_request.pk:
            qs = qs.exclude(pk=exclude_request.pk)
        return qs.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    def clean(self):
        """
        The balance-validation algorithm:
        new allocation must not push total allocated beyond the
        budget's total_amount. Excludes this instance's own previous
        amount when editing an existing allocation (so re-saving an
        unchanged allocation doesn't double-count itself).
        """
        if self.budget_id is None or self.allocated_amount is None:
            return

        existing_total = self.budget.allocations.exclude(pk=self.pk).aggregate(
            total=models.Sum("allocated_amount")
        )["total"] or Decimal("0.00")

        prospective_total = existing_total + self.allocated_amount

        if prospective_total > self.budget.total_amount:
            remaining = self.budget.total_amount - existing_total
            raise ValidationError(
                f"This allocation of {self.allocated_amount} exceeds the "
                f"budget's remaining balance of {remaining}."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
