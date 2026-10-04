from django.conf import settings
from django.db import models


class Document(models.Model):
    """
    A supporting file attached to an ExpenseRequest -- either a
    receipt/bill the Member attaches when submitting, or proof of
    payment the Treasurer attaches when marking a request Paid.

    Kept as a direct ForeignKey (not a GenericForeignKey) since the
    project's scope only requires documents on expense requests --
    simpler to read and defend than contenttypes machinery.
    """

    TYPE_RECEIPT = "receipt"
    TYPE_PAYMENT_PROOF = "payment_proof"
    TYPE_OTHER = "other"

    DOCUMENT_TYPE_CHOICES = [
        (TYPE_RECEIPT, "Receipt / Bill"),
        (TYPE_PAYMENT_PROOF, "Payment Proof"),
        (TYPE_OTHER, "Other"),
    ]

    expense_request = models.ForeignKey(
        "requests_app.ExpenseRequest", on_delete=models.CASCADE, related_name="documents"
    )
    file = models.FileField(upload_to="documents/%Y/%m/")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default=TYPE_RECEIPT)
    description = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="documents_uploaded"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_document_type_display()} for {self.expense_request}"


class AuditLog(models.Model):
    """
    A single record of a significant financial action. Written by
    log_action() (see audit_app/utils.py), called from every
    state-changing view across funds/budgets/requests_app -- this is
    what generates the audit trail the project report describes.

    target_type/target_id identify what was acted on (e.g.
    "FundReceipt" #4) without needing a GenericForeignKey -- kept
    simple and readable, matching the direct style used elsewhere in
    this project.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_actions"
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        who = self.user.username if self.user else "system"
        return f"{who} {self.action} {self.target_type}#{self.target_id} at {self.timestamp}"
