# apps/monitoring/admin_urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("server/", views.server_metrics, name="server-metrics"),
    path("db/", views.db_metrics, name="db-metrics"),
]
