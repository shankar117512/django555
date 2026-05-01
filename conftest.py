# tests/conftest.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an authenticated DRF test client."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="adminpassword123!",
    )


@pytest.fixture
def regular_user(db):
    """Create and return a regular user."""
    return User.objects.create_user(
        username="testuser",
        email="user@test.com",
        password="userpassword123!",
    )


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Return an API client authenticated as regular user."""
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client
