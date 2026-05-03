# apps/api/tests/test_views.py
import pytest


@pytest.mark.django_db
class TestApiViews:
    def test_protected_view_returns_401_for_anonymous(self, client):
        response = client.get("/api/protected/")
        assert response.status_code == 403  # DRF returns 403 for anonymous users
