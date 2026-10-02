from django.contrib import admin
from .models import ExpenseRequest


@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(admin.ModelAdmin):
    list_display = ("purpose", "allocation", "amount", "status", "requested_by", "created_at")
    list_filter = ("status",)
    readonly_fields = ("verified_by", "verified_at", "approved_by", "approved_at", "rejected_by")
