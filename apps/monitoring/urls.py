# apps/monitoring/urls.py
# FIX: import DbMetricsView (class) instead of db_metrics (function)
from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.health_check, name="health-check"),
    path("ping/", views.ping, name="ping"),
    path("db/", views.DbMetricsView.as_view(), name="db-metrics"),  # ← changed
    path("server/", views.ServerMetricsView.as_view(), name="server-metrics"),
]
