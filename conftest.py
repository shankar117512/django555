# conftest.py  ← project root (same level as manage.py)
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def mock_conn():
    # ✅ Now works because connection is a module-level name in views.py
    with patch("apps.monitoring.views.connection") as mock:
        # Ensure the context manager (__enter__/__exit__) works for `with connection.cursor()`
        cursor_mock = MagicMock()
        mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        yield mock


@pytest.fixture
def mock_cache():
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


@pytest.fixture
def admin_client(db):
    admin = User.objects.create_superuser(
        username="adminuser", password="adminpass123", email="admin@example.com"
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client
