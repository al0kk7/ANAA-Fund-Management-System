from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, redirect

from .models import Profile


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    """
    Role-aware landing page. Each role sees a different set of
    quick actions -- this view itself does no restricting, it just
    reads the profile to decide what to show/link to.

    Also computes org-wide fund summary numbers, shown to every role
    (transparency by design, matching the rest of the system). These
    are two independent figures -- see the README for why:
      - total_allocated / unallocated: Budget vs its Allocations
      - total_committed / uncommitted: Allocations vs Approved+Paid
        ExpenseRequests
    """
    # Imported here (not at module level) to avoid a circular import,
    # since funds/budgets/requests_app don't otherwise depend on
    # accounts.
    from funds.models import FundReceipt
    from budgets.models import Allocation
    from requests_app.models import ExpenseRequest

    profile = getattr(request.user, "profile", None)

    total_received = FundReceipt.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_allocated = Allocation.objects.aggregate(total=Sum("allocated_amount"))["total"] or Decimal("0.00")
    total_committed = ExpenseRequest.objects.filter(
        status__in=[ExpenseRequest.STATUS_APPROVED, ExpenseRequest.STATUS_PAID]
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_paid = ExpenseRequest.objects.filter(
        status=ExpenseRequest.STATUS_PAID
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    unallocated = total_received - total_allocated

    summary = {
        "total_received": total_received,
        "total_allocated": total_allocated,
        "unallocated": unallocated,
        "unallocated_abs": abs(unallocated),
        "total_committed": total_committed,
        "uncommitted": total_allocated - total_committed,
        "total_paid": total_paid,
    }

    context = {"profile": profile, "summary": summary}
    return render(request, "accounts/dashboard.html", context)