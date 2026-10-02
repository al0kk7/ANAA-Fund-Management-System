from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import Profile
from .models import ExpenseRequest
from .forms import ExpenseRequestForm, RejectionForm


@login_required
def request_list(request):
    """
    Transparency by design: everyone sees every request. What
    differs by role is which ACTIONS are available on each row --
    decided in the template by checking request.user.profile.
    """
    requests_qs = ExpenseRequest.objects.select_related(
        "allocation", "allocation__budget__event", "requested_by"
    ).all()
    return render(request, "requests_app/request_list.html", {"requests": requests_qs})


@role_required(Profile.ROLE_MEMBER_REQUESTER)
def request_create(request):
    if request.method == "POST":
        form = ExpenseRequestForm(request.POST)
        if form.is_valid():
            expense_request = form.save(commit=False)
            expense_request.requested_by = request.user
            expense_request.status = ExpenseRequest.STATUS_SUBMITTED
            expense_request.save()
            messages.success(request, "Expense request submitted.")
            return redirect("requests_app:request_list")
    else:
        form = ExpenseRequestForm()
    return render(request, "requests_app/request_form.html", {"form": form})


@role_required(Profile.ROLE_TREASURER_ADMIN)
def request_verify(request, pk):
    """
    Treasurer/Admin action: moves a Submitted request to Verified,
    or Rejected with a reason. Only reachable via POST from the list
    page's inline buttons.
    """
    expense_request = get_object_or_404(ExpenseRequest, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "verify":
                expense_request.transition_to(ExpenseRequest.STATUS_VERIFIED, request.user)
                messages.success(request, "Request verified.")
            elif action == "reject":
                form = RejectionForm(request.POST)
                if form.is_valid():
                    expense_request.transition_to(
                        ExpenseRequest.STATUS_REJECTED, request.user,
                        reason=form.cleaned_data["reason"]
                    )
                    messages.success(request, "Request rejected.")
        except ValidationError as e:
            messages.error(request, str(e.message) if hasattr(e, "message") else str(e))

    return redirect("requests_app:request_list")


@role_required(Profile.ROLE_COMMITTEE_APPROVER)
def request_approve(request, pk):
    """
    Committee/Approver action: moves a Verified request to Approved
    (running the balance check against the allocation), or Rejected.
    """
    expense_request = get_object_or_404(ExpenseRequest, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "approve":
                expense_request.transition_to(ExpenseRequest.STATUS_APPROVED, request.user)
                messages.success(request, "Request approved.")
            elif action == "reject":
                form = RejectionForm(request.POST)
                if form.is_valid():
                    expense_request.transition_to(
                        ExpenseRequest.STATUS_REJECTED, request.user,
                        reason=form.cleaned_data["reason"]
                    )
                    messages.success(request, "Request rejected.")
        except ValidationError as e:
            messages.error(request, str(e.message) if hasattr(e, "message") else str(e))

    return redirect("requests_app:request_list")
