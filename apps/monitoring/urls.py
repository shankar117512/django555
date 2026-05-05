# apps/monitoring/urls.py
from django.urls import path

from apps.monitoring.views import db_metrics, health_check, ping, server_metrics

app_name = "monitoring"

urlpatterns = [
    path("", health_check, name="health-check"),
    path("ping/", ping, name="ping"),
    path("db/", db_metrics, name="db-metrics"),
    path("server/", server_metrics, name="server-metrics"),
]
