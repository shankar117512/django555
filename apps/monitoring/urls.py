# apps/monitoring/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("server/", views.server_metrics, name="server-metrics"),
    path("database/", views.db_metrics, name="db-metrics"),
    path("tenants/", views.tenant_metrics, name="tenant-metrics"),
]
