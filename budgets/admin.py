from django.contrib import admin
from .models import Event, Budget, Allocation, EventExpense


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


@admin.register(EventExpense)
class EventExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "event", "amount", "expense_date", "added_by")
    list_filter = ("event",)
    date_hierarchy = "expense_date"
