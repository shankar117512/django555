# apps/api/urls.py
from django.urls import include, path

from . import views

app_name = "api"

urlpatterns = [
    path("protected/", views.ProtectedView.as_view(), name="protected"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("orders/", include("orders.urls", namespace="orders")),
]
