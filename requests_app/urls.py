from django.urls import path
from . import views

app_name = "requests_app"

urlpatterns = [
    path("", views.request_list, name="request_list"),
    path("new/", views.request_create, name="request_create"),
    path("<int:pk>/verify/", views.request_verify, name="request_verify"),
    path("<int:pk>/approve/", views.request_approve, name="request_approve"),
    path(
        "<int:pk>/pay/",
        views.request_pay,
        name="request_pay"
    ),
]
