# apps/monitoring/urls.py
from django.urls import path

from .views import db_metrics, health_check, server_metrics

urlpatterns = [
    path("health/", health_check),
    path("server/", server_metrics),
    path("db/", db_metrics),
]
