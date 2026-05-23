# apps/api/tests/test_views.py
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient  # ← use DRF's client, not Django's


@pytest.mark.django_db
class TestProtectedView:
    def test_protected_view_unauthenticated(self):
        client = APIClient()
        with patch(
            "apps.core.middleware.TenantMainMiddleware.process_request",
            return_value=None,
        ):
            response = client.get("/api/protected/")
        assert response.status_code == 401

    def test_protected_view_authenticated(self, django_user_model):
        client = APIClient()
        user = django_user_model.objects.create_user(
            username="testuser", password="testpass"
        )
        client.force_authenticate(user=user)  # ← DRF-aware auth bypass
        with patch(
            "apps.core.middleware.TenantMainMiddleware.process_request",
            return_value=None,
        ):
            response = client.get("/api/protected/")
        assert response.status_code == 200
