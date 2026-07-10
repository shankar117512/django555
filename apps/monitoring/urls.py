# apps/monitoring/urls.py
from django.urls import path

from . import views
from .views import ActivityLogListView, DashboardMetricsView, ServerMetricsView

app_name = "monitoring"

urlpatterns = [
    path("", views.health_check, name="health-check"),
    path("ping/", views.ping, name="ping"),
    path("db/", views.db_metrics, name="db-metrics"),
    path("server/", ServerMetricsView.as_view(), name="server-metrics"),
    path("dashboard/", DashboardMetricsView.as_view(), name="dashboard_metrics"),
    path("activity/", ActivityLogListView.as_view(), name="activity_log"),
]
