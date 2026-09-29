from django.contrib import admin
from .models import FundSource, FundReceipt


@admin.register(FundSource)
class FundSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "total_received")
    list_filter = ("source_type",)


@admin.register(FundReceipt)
class FundReceiptAdmin(admin.ModelAdmin):
    list_display = ("source", "amount", "received_date", "payer_name", "recorded_by")
    list_filter = ("source", "received_date")
    date_hierarchy = "received_date"
