import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import Profile
from audit_app.utils import log_action
from .models import Event, Budget, Allocation, EventExpense
from .forms import EventForm, BudgetForm, AllocationForm, EventExpenseForm


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

    actual_expenses = event.actual_expenses.select_related("added_by").all()

    profile = getattr(request.user, "profile", None)
    can_add_expense = bool(
        profile
        and not event.is_closed
        and (profile.is_secretary() or profile.is_treasurer_admin())
    )

    context = {
        "event": event,
        "budgets": budgets,
        "allocations": allocations,
        "expense_requests": expense_requests,
        "actual_expenses": actual_expenses,
        "can_add_expense": can_add_expense,
        "expense_form": EventExpenseForm() if can_add_expense else None,
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


@role_required(Profile.ROLE_SECRETARY, Profile.ROLE_TREASURER_ADMIN)
def event_expense_add(request, pk):
    """
    Records one actual expense (with optional scanned bill) against an
    event, after the fact. This is the Secretary's job (they also
    submit the original expense requests) -- Treasurer/Admin can also
    add. The Committee/Approver role is view-only here by design.

    Blocked once the event is Closed: a closed event is the final
    record, so nothing may be added to it afterwards.
    """
    event = get_object_or_404(Event, pk=pk)

    if event.is_closed:
        messages.error(request, "This event is closed -- no more expenses can be added.")
        return redirect("budgets:event_detail", pk=pk)

    if request.method == "POST":
        form = EventExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.event = event
            expense.added_by = request.user
            expense.save()
            log_action(
                request.user, "recorded expense", expense,
                description=f"NPR {expense.amount} - {expense.description} ({event.name})"
            )
            messages.success(request, "Expense recorded.")
        else:
            for field, errors in form.errors.items():
                prefix = "" if field == "__all__" else f"{form[field].label}: "
                for error in errors:
                    messages.error(request, f"{prefix}{error}")

    return redirect("budgets:event_detail", pk=pk)


@login_required
def event_expense_delete(request, pk):
    """
    Removes a wrongly-entered expense. Allowed for the person who
    added it or the Treasurer/Admin, and only while the event is
    still open. The deletion itself is written to the audit trail,
    so nothing disappears without a record that it did.
    """
    expense = get_object_or_404(EventExpense, pk=pk)
    event = expense.event
    profile = getattr(request.user, "profile", None)

    is_adder = expense.added_by_id == request.user.id
    is_treasurer = bool(profile and profile.is_treasurer_admin())
    if not (is_adder or is_treasurer):
        return HttpResponseForbidden("You can only delete expenses you added yourself.")

    if event.is_closed:
        messages.error(request, "This event is closed -- its expenses can no longer be changed.")
        return redirect("budgets:event_detail", pk=event.pk)

    if request.method == "POST":
        description = f"NPR {expense.amount} - {expense.description} ({event.name})"
        log_action(request.user, "deleted expense", expense, description=description)
        expense.delete()
        messages.success(request, "Expense deleted.")

    return redirect("budgets:event_detail", pk=event.pk)


@login_required
def annual_audit(request):
    """
    Yearly audit report: every event whose date falls between a
    start and end date chosen by the user, with budgeted / paid-out /
    actual-expense totals per event and grand totals. Defaults to the
    current calendar year. Visible to all logged-in users
    (transparency); designed to be printed.

    Events with no date set can't be placed in a period, so they are
    excluded from the results but counted in a visible note, rather
    than silently disappearing from the audit.
    """
    today = datetime.date.today()

    def parse_date(value, fallback):
        try:
            return datetime.date.fromisoformat(value)
        except (TypeError, ValueError):
            return fallback

    start = parse_date(request.GET.get("start"), datetime.date(today.year, 1, 1))
    end = parse_date(request.GET.get("end"), datetime.date(today.year, 12, 31))

    date_error = None
    if start > end:
        date_error = "Start date is after the end date -- showing no results."

    events = []
    if not date_error:
        events = (
            Event.objects.filter(event_date__gte=start, event_date__lte=end)
            .prefetch_related("actual_expenses")
            .order_by("event_date")
        )

    rows = []
    grand_budgeted = grand_paid = grand_actual = 0
    for event in events:
        budgeted = event.total_budgeted()
        paid = event.total_spent()
        actual = event.total_actual_expenses()
        grand_budgeted += budgeted
        grand_paid += paid
        grand_actual += actual
        rows.append({
            "event": event,
            "budgeted": budgeted,
            "paid": paid,
            "actual": actual,
            "variance": budgeted - actual,
            "missing_bills": event.expenses_missing_bills(),
            "expenses": event.actual_expenses.all(),
        })

    undated_events = Event.objects.filter(event_date__isnull=True).count()

    context = {
        "start": start,
        "end": end,
        "rows": rows,
        "grand_budgeted": grand_budgeted,
        "grand_paid": grand_paid,
        "grand_actual": grand_actual,
        "grand_variance": grand_budgeted - grand_actual,
        "date_error": date_error,
        "undated_events": undated_events,
        "this_year": today.year,
        "last_year": today.year - 1,
    }
    return render(request, "budgets/annual_audit.html", context)
