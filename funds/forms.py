from django import forms
from .models import FundSource, FundReceipt


class FundSourceForm(forms.ModelForm):
    class Meta:
        model = FundSource
        fields = ["name", "source_type", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2"}),
            "source_type": forms.Select(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2"}),
            "description": forms.Textarea(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2", "rows": 3}),
        }


class FundReceiptForm(forms.ModelForm):
    class Meta:
        model = FundReceipt
        fields = ["source", "amount", "received_date", "payer_name", "notes"]
        widgets = {
            "source": forms.Select(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2"}),
            "amount": forms.NumberInput(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2", "step": "0.01"}),
            "received_date": forms.DateInput(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2", "type": "date"}),
            "payer_name": forms.TextInput(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2"}),
            "notes": forms.Textarea(attrs={"class": "w-full border border-slate-300 rounded px-3 py-2", "rows": 2}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
