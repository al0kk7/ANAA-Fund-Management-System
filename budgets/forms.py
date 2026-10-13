from django import forms
from django.core.exceptions import ValidationError
from .models import Event, Budget, Allocation, EventExpense

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
    # form.non_field_errors() on its own. Adding a manual call here
    # previously caused the same error to be validated and displayed
    # twice.


class EventExpenseForm(forms.ModelForm):
    """
    Records one real expense (one bill) against an event, after the
    fact. The scanned bill is optional at entry time so an expense
    can be logged immediately and the scan added once available --
    but the event page flags any expense still missing a bill, so
    nothing quietly goes undocumented.
    """
    class Meta:
        model = EventExpense
        fields = ["description", "amount", "expense_date", "paid_to", "physical_reference", "bill_file"]
        widgets = {
            "description": forms.TextInput(attrs={"class": INPUT, "placeholder": "e.g. Hall booking, Catering, Banner printing"}),
            "amount": forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}),
            "expense_date": forms.DateInput(attrs={"class": INPUT, "type": "date"}),
            "paid_to": forms.TextInput(attrs={"class": INPUT, "placeholder": "Vendor / shop / person (optional)"}),
            "physical_reference": forms.TextInput(attrs={"class": INPUT, "placeholder": "Where the paper bill is filed (optional)"}),
            "bill_file": forms.ClearableFileInput(attrs={"class": INPUT}),
        }
        labels = {"bill_file": "Scanned / photographed bill"}
