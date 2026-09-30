from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.decorators import role_required
from accounts.models import Profile
from .models import Event, Budget, Allocation
from .forms import EventForm, BudgetForm, AllocationForm


@login_required
def event_list(request):
    events = Event.objects.all().order_by("-event_date")
    return render(request, "budgets/event_list.html", {"events": events})


@role_required(Profile.ROLE_TREASURER_ADMIN)
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Event created.")
            return redirect("budgets:event_list")
    else:
        form = EventForm()
    return render(request, "budgets/event_form.html", {"form": form})


@login_required
def budget_list(request):
    budgets = Budget.objects.select_related("event").all()
    return render(request, "budgets/budget_list.html", {"budgets": budgets})


@role_required(Profile.ROLE_TREASURER_ADMIN)
def budget_create(request):
    if request.method == "POST":
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.created_by = request.user
            budget.save()
            messages.success(request, "Budget created.")
            return redirect("budgets:budget_list")
    else:
        form = BudgetForm()

    if not Event.objects.exists():
        messages.error(request, "Create at least one Event before creating a budget.")

    return render(request, "budgets/budget_form.html", {"form": form})


@login_required
def allocation_list(request):
    allocations = Allocation.objects.select_related("budget", "budget__event").all()
    return render(request, "budgets/allocation_list.html", {"allocations": allocations})


@role_required(Profile.ROLE_TREASURER_ADMIN)
def allocation_create(request):
    if request.method == "POST":
        form = AllocationForm(request.POST)
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.created_by = request.user
            allocation.save()
            messages.success(request, "Allocation created.")
            return redirect("budgets:allocation_list")
        
    else:
        form = AllocationForm()

    if not Budget.objects.exists():
        messages.error(request, "Create at least one Budget before creating an allocation.")

    return render(request, "budgets/allocation_form.html", {"form": form})
