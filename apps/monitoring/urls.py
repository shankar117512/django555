# apps/monitoring/urls.py
from django.urls import path

from apps.monitoring.views import health_check

urlpatterns = [
    path("", health_check, name="health-check"),  # ← was path("health/", ...)
]
