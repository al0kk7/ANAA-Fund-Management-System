from django.conf import settings
from django.db import models


class FundSource(models.Model):
    """
    A category/origin of money coming into ANAA -- e.g. "2026 Membership
    Fees", "Annual Gala Sponsorship". Created once, then FundReceipts
    are recorded against it as money actually arrives.
    """

    TYPE_MEMBERSHIP_FEE = "membership_fee"
    TYPE_DONATION = "donation"
    TYPE_EVENT_TICKET = "event_ticket"
    TYPE_SPONSORSHIP = "sponsorship"
    TYPE_OTHER = "other"

    SOURCE_TYPE_CHOICES = [
        (TYPE_MEMBERSHIP_FEE, "Membership Fee"),
        (TYPE_DONATION, "Donation"),
        (TYPE_EVENT_TICKET, "Event Ticket Sales"),
        (TYPE_SPONSORSHIP, "Sponsorship"),
        (TYPE_OTHER, "Other"),
    ]

    name = models.CharField(max_length=150)
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"

    def total_received(self):
        """Sum of all receipts recorded against this source."""
        return self.receipts.aggregate(
            total=models.Sum("amount")
        )["total"] or 0


class FundReceipt(models.Model):
    """
    A single instance of money actually received -- e.g. one donor's
    transfer, one batch of membership fee payments. Always linked to
    a FundSource and to the Treasurer/Admin user who recorded it.
    """

    source = models.ForeignKey(FundSource, on_delete=models.PROTECT, related_name="receipts")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    received_date = models.DateField()
    payer_name = models.CharField(max_length=150, blank=True, help_text="Donor/payer name, if known")
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="fund_receipts_recorded"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_date", "-created_at"]

    def __str__(self):
        return f"{self.amount} from {self.source.name} on {self.received_date}"
