# apps/core/urls.py
from django.urls import path

from . import views

app_name = "core"  # ← add this

urlpatterns = [
    path("", views.home_view, name="home"),
]
