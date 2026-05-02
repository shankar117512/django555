# conftest.py
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def mock_conn():
    with patch("django.db.connection.cursor") as mock:
        yield mock


@pytest.fixture
def mock_cache():
    with patch("django.core.cache.cache") as mock:
        yield mock


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    user = User.objects.create_user(username="testuser", password="testpass123")
    client = APIClient()  # or Django Client()
    client.force_authenticate(user=user)  # DRF
    return client
