# apps/monitoring/urls.py
from django.urls import path

from apps.monitoring.views import db_metrics, health_check, server_metrics

urlpatterns = [
    path("", health_check, name="health-check"),  # /monitoring/
    path("db/", db_metrics, name="db-metrics"),  # /monitoring/db/
    path("server/", server_metrics, name="server-metrics"),
]
