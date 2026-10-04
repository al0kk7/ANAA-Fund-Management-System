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
