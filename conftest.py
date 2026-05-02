# conftest.py
# conftest.py  ← place this in your PROJECT ROOT (same level as manage.py)
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def mock_conn():
    # ✅ Fix 5: patch where it's actually used in your view
    with patch("apps.monitoring.views.connection") as mock:
        yield mock


@pytest.fixture
def mock_cache():
    # ✅ patch where cache is used in your view
    with patch("apps.monitoring.views.cache") as mock:
        yield mock


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    user = User.objects.create_user(username="testuser", password="testpass123")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ✅ Fix 1: Added missing admin_client fixture
@pytest.fixture
def admin_client(db):
    admin = User.objects.create_superuser(
        username="adminuser", password="adminpass123", email="admin@example.com"
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client
