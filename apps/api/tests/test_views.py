# apps/api/tests/test_views.py
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def authenticated_client(db):
    user = User.objects.create_user(username="testuser", password="pass")
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.mark.django_db
class TestProtectedView:
    def test_protected_view_unauthenticated(self, client):
        response = client.get(reverse("api:protected"))
        assert response.status_code == 401

    def test_protected_view_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse("api:protected"))
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "authenticated"
        assert "user" in data
