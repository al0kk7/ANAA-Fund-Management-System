from django.urls import path
from . import views

app_name = "budgets"

urlpatterns = [
    path("events/", views.event_list, name="event_list"),
    path("events/new/", views.event_create, name="event_create"),
    path("budgets/", views.budget_list, name="budget_list"),
    path("budgets/new/", views.budget_create, name="budget_create"),
    path("allocations/", views.allocation_list, name="allocation_list"),
    path("allocations/new/", views.allocation_create, name="allocation_create"),
]
