# apps/monitoring/tests/test_views.py
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestMonitoringViews:
    def test_health_check(self, client):
        response = client.get(reverse("monitoring:health-check"))
        assert response.status_code == 200
