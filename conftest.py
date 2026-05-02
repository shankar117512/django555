# conftest.py
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


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
