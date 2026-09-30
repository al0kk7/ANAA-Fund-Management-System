from django.contrib import admin
from .models import Event, Budget, Allocation


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "event_date")


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("event", "total_amount", "total_allocated", "remaining_balance", "created_by")


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ("purpose", "budget", "allocated_amount", "created_by")
    list_filter = ("budget",)
