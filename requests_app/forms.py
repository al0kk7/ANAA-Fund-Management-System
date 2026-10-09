from django import forms
from django.core.exceptions import ValidationError
from .models import ExpenseRequest

INPUT = "w-full border border-slate-300 rounded px-3 py-2"


class ExpenseRequestForm(forms.ModelForm):
    supporting_document = forms.FileField(
        required=False,
        label="Receipt / Bill (optional)",
        widget=forms.ClearableFileInput(attrs={"class": INPUT}),
    )

    class Meta:
        model = ExpenseRequest
        fields = ["allocation", "amount", "purpose", "description"]
        widgets = {
            "allocation": forms.Select(attrs={"class": INPUT}),
            "amount": forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}),
            "purpose": forms.TextInput(attrs={"class": INPUT}),
            "description": forms.Textarea(attrs={"class": INPUT, "rows": 3}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount


class RejectionForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": INPUT, "rows": 2, "placeholder": "Reason for rejection"}),
        required=True,
        label="Rejection reason",
    )


class PaymentForm(forms.Form):
    payment_proof = forms.FileField(
        required=False,
        label="Payment proof (optional)",
        widget=forms.ClearableFileInput(attrs={"class": INPUT}),
    )


class AddDocumentForm(forms.Form):
    """
    For attaching a document to an ExpenseRequest after it has
    already been submitted -- separate from ExpenseRequestForm
    (initial submission) and PaymentForm (payment proof at the pay
    step), since this one can be used by the Member at any time.
    """
    file = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={"class": "text-xs"}),
    )
    document_type = forms.ChoiceField(
        choices=[
            ("receipt", "Receipt / Bill"),
            ("payment_proof", "Payment Proof"),
            ("other", "Other"),
        ],
        widget=forms.Select(attrs={"class": "text-xs border border-slate-300 rounded"}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "text-xs border border-slate-300 rounded px-1", "placeholder": "Note (optional)"}),
    )
