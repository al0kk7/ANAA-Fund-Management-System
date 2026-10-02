from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from budgets.models import Allocation


class ExpenseRequest(models.Model):
    """
    A Member/Requester's request to spend money from a specific
    Allocation. Moves through a fixed set of states, enforced by
    ALLOWED_TRANSITIONS below -- this is the state-transition
    validation algorithm documented in the project report.
    """

    STATUS_SUBMITTED = "submitted"
    STATUS_VERIFIED = "verified"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PAID = "paid"

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_VERIFIED, "Verified"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_PAID, "Paid"),
    ]

    # Which transitions are legal from a given status. Enforced in
    # transition_to() below -- e.g. a request cannot jump straight
    # from "submitted" to "approved" without passing through
    # "verified" first.
    ALLOWED_TRANSITIONS = {
        STATUS_SUBMITTED: [STATUS_VERIFIED, STATUS_REJECTED],
        STATUS_VERIFIED: [STATUS_APPROVED, STATUS_REJECTED],
        STATUS_APPROVED: [STATUS_PAID],
        STATUS_REJECTED: [],  # terminal state
        STATUS_PAID: [],      # terminal state
    }

    allocation = models.ForeignKey(Allocation, on_delete=models.PROTECT, related_name="expense_requests")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="expense_requests_made"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expense_requests_verified"
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expense_requests_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expense_requests_rejected"
    )
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.purpose} - {self.amount} ({self.get_status_display()})"

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status, user, reason=""):
        """
        The state-transition validation algorithm. Raises
        ValidationError on any illegal transition instead of silently
        allowing it -- this is what a view calls, never setting
        .status directly.
        """
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"Cannot move a request from '{self.get_status_display()}' "
                f"to '{dict(self.STATUS_CHOICES).get(new_status, new_status)}'."
            )

        from django.utils import timezone

        if new_status == self.STATUS_VERIFIED:
            self.verified_by = user
            self.verified_at = timezone.now()

        elif new_status == self.STATUS_APPROVED:
            # Balance check happens at approval time -- this is the
            # point the money is actually committed against the
            # allocation, not at submission time.
            remaining = self.allocation.allocated_amount - self.allocation.total_approved_or_paid(
                exclude_request=self
            )
            if self.amount > remaining:
                raise ValidationError(
                    f"This request of {self.amount} exceeds the allocation's "
                    f"remaining balance of {remaining}."
                )
            self.approved_by = user
            self.approved_at = timezone.now()

        elif new_status == self.STATUS_REJECTED:
            self.rejected_by = user
            self.rejection_reason = reason

        elif new_status == self.STATUS_PAID:
            pass  # payment recording detail arrives in a later iteration

        self.status = new_status
        self.save()
