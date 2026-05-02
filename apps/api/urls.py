# apps/api/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("protected/", views.protected_view, name="api-protected"),
]
