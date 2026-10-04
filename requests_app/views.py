from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import Profile
from audit_app.utils import log_action
from audit_app.models import Document
from .models import ExpenseRequest
from .forms import ExpenseRequestForm, RejectionForm, PaymentForm


@login_required
def request_list(request):
    """
    Transparency by design: everyone sees every request, including
    its attached documents. What differs by role is which ACTIONS
    are available on each row -- decided in the template by checking
    request.user.profile.
    """
    requests_qs = ExpenseRequest.objects.select_related(
        "allocation", "allocation__budget__event", "requested_by"
    ).prefetch_related("documents").all()
    return render(request, "requests_app/request_list.html", {"requests": requests_qs})


@role_required(Profile.ROLE_MEMBER_REQUESTER)
def request_create(request):
    if request.method == "POST":
        form = ExpenseRequestForm(request.POST, request.FILES)
        if form.is_valid():
            expense_request = form.save(commit=False)
            expense_request.requested_by = request.user
            expense_request.status = ExpenseRequest.STATUS_SUBMITTED
            expense_request.save()

            uploaded_file = form.cleaned_data.get("supporting_document")
            if uploaded_file:
                Document.objects.create(
                    expense_request=expense_request,
                    file=uploaded_file,
                    document_type=Document.TYPE_RECEIPT,
                    uploaded_by=request.user,
                )

            log_action(request.user, "submitted", expense_request, description=f"NPR {expense_request.amount} for {expense_request.purpose}")
            messages.success(request, "Expense request submitted.")
            return redirect("requests_app:request_list")
    else:
        form = ExpenseRequestForm()
    return render(request, "requests_app/request_form.html", {"form": form})


@role_required(Profile.ROLE_TREASURER_ADMIN)
def request_verify(request, pk):
    """
    Treasurer/Admin action: moves a Submitted request to Verified,
    or Rejected with a reason.
    """
    expense_request = get_object_or_404(ExpenseRequest, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "verify":
                expense_request.transition_to(ExpenseRequest.STATUS_VERIFIED, request.user)
                log_action(request.user, "verified", expense_request)
                messages.success(request, "Request verified.")
            elif action == "reject":
                form = RejectionForm(request.POST)
                if form.is_valid():
                    expense_request.transition_to(
                        ExpenseRequest.STATUS_REJECTED, request.user,
                        reason=form.cleaned_data["reason"]
                    )
                    log_action(request.user, "rejected", expense_request, description=form.cleaned_data["reason"])
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
                log_action(request.user, "approved", expense_request)
                messages.success(request, "Request approved.")
            elif action == "reject":
                form = RejectionForm(request.POST)
                if form.is_valid():
                    expense_request.transition_to(
                        ExpenseRequest.STATUS_REJECTED, request.user,
                        reason=form.cleaned_data["reason"]
                    )
                    log_action(request.user, "rejected", expense_request, description=form.cleaned_data["reason"])
                    messages.success(request, "Request rejected.")
        except ValidationError as e:
            messages.error(request, str(e.message) if hasattr(e, "message") else str(e))

    return redirect("requests_app:request_list")


@role_required(Profile.ROLE_TREASURER_ADMIN)
def request_pay(request, pk):
    """
    Treasurer/Admin action: the final transition, Approved -> Paid.
    Optionally attaches payment proof at this step.
    """
    expense_request = get_object_or_404(ExpenseRequest, pk=pk)

    if request.method == "POST":
        try:
            expense_request.transition_to(ExpenseRequest.STATUS_PAID, request.user)

            form = PaymentForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = form.cleaned_data.get("payment_proof")
                if uploaded_file:
                    Document.objects.create(
                        expense_request=expense_request,
                        file=uploaded_file,
                        document_type=Document.TYPE_PAYMENT_PROOF,
                        uploaded_by=request.user,
                    )

            log_action(request.user, "marked paid", expense_request, description=f"NPR {expense_request.amount}")
            messages.success(request, "Request marked as paid successfully.")
        except ValidationError as e:
            messages.error(request, str(e.message) if hasattr(e, "message") else str(e))

    return redirect("requests_app:request_list")
