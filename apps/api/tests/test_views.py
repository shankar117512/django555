# apps/api/tests/test_views.py
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAPIHealth:
    def test_health_check_returns_200(self, api_client):
        url = "/health/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_metrics_endpoint_accessible(self, api_client):
        url = "/metrics/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAuthentication:
    def test_unauthenticated_access_denied(self, api_client):
        url = "/api/v1/"
        response = api_client.get(url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_authenticated_access_allowed(self, authenticated_client):
        url = "/api/v1/"
        response = authenticated_client.get(url)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
