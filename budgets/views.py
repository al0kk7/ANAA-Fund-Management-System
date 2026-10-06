from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import Profile
from audit_app.utils import log_action
from .models import Event, Budget, Allocation
from .forms import EventForm, BudgetForm, AllocationForm


@login_required
def event_list(request):
    events = Event.objects.all().order_by("-event_date")
    return render(request, "budgets/event_list.html", {"events": events})


@login_required
def event_detail(request, pk):
    """
    The project closure report: every budget, allocation, and expense
    request (with its attached documents) under one event, plus the
    final totals. Visible to everyone (transparency); only
    Treasurer/Admin sees the "Close Event" action.
    """
    from requests_app.models import ExpenseRequest

    event = get_object_or_404(Event, pk=pk)
    budgets = event.budgets.all()
    allocations = Allocation.objects.filter(budget__event=event).select_related("budget")
    expense_requests = ExpenseRequest.objects.filter(
        allocation__budget__event=event
    ).select_related("allocation", "requested_by").prefetch_related("documents")

    context = {
        "event": event,
        "budgets": budgets,
        "allocations": allocations,
        "expense_requests": expense_requests,
    }
    return render(request, "budgets/event_detail.html", context)


@role_required(Profile.ROLE_TREASURER_ADMIN)
def event_close(request, pk):
    """
    Marks an event Closed -- the final step of the workflow
    (Settled/Audited in the project's state diagram). Only sensible
    once every expense request under the event has reached a final
    state (Paid or Rejected); blocks closure otherwise so a project
    can't be "closed" while money is still in flight.
    """
    from requests_app.models import ExpenseRequest

    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        unfinished = ExpenseRequest.objects.filter(
            allocation__budget__event=event
        ).exclude(status__in=[ExpenseRequest.STATUS_PAID, ExpenseRequest.STATUS_REJECTED])

        if unfinished.exists():
            messages.error(
                request,
                f"Cannot close this event -- {unfinished.count()} expense request(s) "
                f"are still in progress (not yet Paid or Rejected)."
            )
        else:
            event.is_closed = True
            event.closed_by = request.user
            from django.utils import timezone
            event.closed_at = timezone.now()
            event.closure_notes = request.POST.get("closure_notes", "")
            event.save()
            log_action(request.user, "closed", event, description=f"Final leftover: NPR {event.total_leftover()}")
            messages.success(request, "Event closed. This is now a final record.")

    return redirect("budgets:event_detail", pk=pk)


@role_required(Profile.ROLE_TREASURER_ADMIN)
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            log_action(request.user, "created", event)
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
            log_action(request.user, "created", budget, description=f"NPR {budget.total_amount} for {budget.event.name}")
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
            log_action(request.user, "created", allocation, description=f"NPR {allocation.allocated_amount} for {allocation.purpose}")
            messages.success(request, "Allocation created.")
            return redirect("budgets:allocation_list")
        # else: fall through and re-render with form.non_field_errors()
        # shown inline (see allocation_form.html) -- no need to also
        # push the same message through the messages framework.
    else:
        form = AllocationForm()

    if not Budget.objects.exists():
        messages.error(request, "Create at least one Budget before creating an allocation.")

    return render(request, "budgets/allocation_form.html", {"form": form})
