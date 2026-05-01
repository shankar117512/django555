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
