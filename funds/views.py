from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import Profile
from .models import FundSource, FundReceipt
from .forms import FundSourceForm, FundReceiptForm


@login_required
def source_list(request):
    """
    Visible to everyone logged in (transparency by design) -- but
    only Treasurer/Admin gets the "Add Source" action, enforced both
    in the template (hidden link) and on the create view itself
    (role_required decorator), per the security checklist.
    """
    sources = FundSource.objects.all().order_by("name")
    total_all_sources = FundReceipt.objects.aggregate(total=Sum("amount"))["total"] or 0
    return render(request, "funds/source_list.html", {
        "sources": sources,
        "total_all_sources": total_all_sources,
    })


@role_required(Profile.ROLE_TREASURER_ADMIN)
def source_create(request):
    if request.method == "POST":
        form = FundSourceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fund source created.")
            return redirect("funds:source_list")
    else:
        form = FundSourceForm()
    return render(request, "funds/source_form.html", {"form": form})


@login_required
def receipt_list(request):
    receipts = FundReceipt.objects.select_related("source", "recorded_by").all()
    return render(request, "funds/receipt_list.html", {"receipts": receipts})


@role_required(Profile.ROLE_TREASURER_ADMIN)
def receipt_create(request):
    if request.method == "POST":
        form = FundReceiptForm(request.POST)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.recorded_by = request.user
            receipt.save()
            messages.success(request, "Fund receipt recorded.")
            return redirect("funds:receipt_list")
    else:
        form = FundReceiptForm()

    if not FundSource.objects.exists():
        messages.error(request, "Create at least one Fund Source before recording a receipt.")

    return render(request, "funds/receipt_form.html", {"form": form})
