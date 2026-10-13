from django.urls import path
from . import views

app_name = "budgets"

urlpatterns = [
    path("events/", views.event_list, name="event_list"),
    path("events/new/", views.event_create, name="event_create"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/<int:pk>/close/", views.event_close, name="event_close"),
    path("events/<int:pk>/expenses/add/", views.event_expense_add, name="event_expense_add"),
    path("expenses/<int:pk>/delete/", views.event_expense_delete, name="event_expense_delete"),
    path("yearly-audit/", views.annual_audit, name="annual_audit"),
    path("budgets/", views.budget_list, name="budget_list"),
    path("budgets/new/", views.budget_create, name="budget_create"),
    path("allocations/", views.allocation_list, name="allocation_list"),
    path("allocations/new/", views.allocation_create, name="allocation_create"),
]
