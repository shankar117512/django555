# apps/monitoring/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("monitoring/server/", views.server_metrics, name="server_metrics"),
    path("monitoring/db/", views.db_metrics, name="db_metrics"),
]
