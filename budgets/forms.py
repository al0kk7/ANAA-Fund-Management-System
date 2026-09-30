from django import forms
from django.core.exceptions import ValidationError
from .models import Event, Budget, Allocation

INPUT = "w-full border border-slate-300 rounded px-3 py-2"


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["name", "description", "event_date"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT}),
            "description": forms.Textarea(attrs={"class": INPUT, "rows": 3}),
            "event_date": forms.DateInput(attrs={"class": INPUT, "type": "date"}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["event", "total_amount", "notes"]
        widgets = {
            "event": forms.Select(attrs={"class": INPUT}),
            "total_amount": forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}),
            "notes": forms.Textarea(attrs={"class": INPUT, "rows": 2}),
        }

    def clean_total_amount(self):
        amount = self.cleaned_data["total_amount"]
        if amount <= 0:
            raise ValidationError("Total amount must be greater than zero.")
        return amount


class AllocationForm(forms.ModelForm):
    class Meta:
        model = Allocation
        fields = ["budget", "purpose", "allocated_amount"]
        widgets = {
            "budget": forms.Select(attrs={"class": INPUT}),
            "purpose": forms.TextInput(attrs={"class": INPUT}),
            "allocated_amount": forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}),
        }

    # No custom clean() needed here: Django's ModelForm already calls
    # self.instance.full_clean() automatically during is_valid() (via
    # _post_clean()), which runs Allocation.clean() -- the balance
    # validation -- and attaches any ValidationError to
    # form.non_field_errors() on its own. A manual call here would
    # run that same validation a second time and double every error.