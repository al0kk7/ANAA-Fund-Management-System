from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Event(models.Model):
    """
    Something ANAA is raising/spending money for -- e.g. "2026 Annual
    Reunion", "Scholarship Program 2026". A Budget is created against
    one Event.
    """
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    event_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Budget(models.Model):
    """
    The total amount approved for an Event. Allocations are then
    carved out of this budget -- the sum of allocations must never
    exceed total_amount (enforced in Allocation.clean()).
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
