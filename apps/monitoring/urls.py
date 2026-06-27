# apps/monitoring/urls.py
from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.health_check, name="health-check"),
    path("ping/", views.ping, name="ping"),
    path("db/", views.db_metrics, name="db-metrics"),
    path("server/", views.ServerMetricsView.as_view(), name="server-metrics"),
]
