# apps/api/tests/test_views.py
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAuthentication:
    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/protected/")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_authenticated_access_allowed(self, authenticated_client):
        response = authenticated_client.get("/api/protected/")
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()
