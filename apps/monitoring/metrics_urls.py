# apps/monitoring/metrics_urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("db/", views.DbMetricsView.as_view(), name="db-metrics"),
    path("server/", views.ServerMetricsView.as_view(), name="server-metrics"),
]
