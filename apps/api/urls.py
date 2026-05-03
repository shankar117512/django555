# apps/api/urls.py
from django.urls import path

from . import views

app_name = "api"  # ← add this

urlpatterns = [
    path("protected/", views.protected_view, name="protected"),
]
