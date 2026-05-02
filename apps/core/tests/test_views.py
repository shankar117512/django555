# apps/core/tests/test_views.py
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestHomeView:
    def test_home_returns_200(self, api_client):
        response = api_client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_home_response_content(self, api_client):
        response = api_client.get("/")
        assert b"successfully" in response.content

    def test_home_no_auth_required(self, api_client):
        """Home page must be publicly accessible."""
        response = api_client.get("/")
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN
