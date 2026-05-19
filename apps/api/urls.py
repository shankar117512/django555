# apps/api/urls.py
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("protected/", views.ProtectedView.as_view(), name="protected"),
]
