from django.contrib import admin
from .models import Document, AuditLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("expense_request", "document_type", "uploaded_by", "uploaded_at")
    list_filter = ("document_type",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "target_type", "target_id", "description")
    list_filter = ("action", "target_type")
    date_hierarchy = "timestamp"
