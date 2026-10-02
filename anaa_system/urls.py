from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('funds/', include('funds.urls')),
    path('budgets/', include('budgets.urls')),
    path('requests/', include('requests_app.urls')),
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
]