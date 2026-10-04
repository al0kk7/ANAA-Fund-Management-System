from django.urls import path
from . import views

app_name = "audit_app"

urlpatterns = [
    path("", views.audit_list, name="audit_list"),
]
