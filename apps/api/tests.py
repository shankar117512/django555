# apps/api/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class ProtectedViewUnauthenticatedTest(TestCase):
    """Unauthenticated requests must be rejected."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api:protected")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_unauthenticated_returns_401_or_405(self):
        response = self.client.post(self.url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_405_METHOD_NOT_ALLOWED],
        )


class ProtectedViewAuthenticatedTest(TestCase):
    """Authenticated requests must succeed and return expected payload."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api:protected")
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_message_key(self):
        response = self.client.get(self.url)
        self.assertIn("message", response.data)

    def test_response_message_is_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["message"], "authenticated")

    def test_response_contains_user_key(self):
        response = self.client.get(self.url)
        self.assertIn("user", response.data)

    def test_response_user_matches_logged_in_user(self):
        response = self.client.get(self.url)
        self.assertIn("testuser", response.data["user"])

    def test_only_get_method_allowed(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_method_not_allowed(self):
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_not_allowed(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ProtectedViewAdminUserTest(TestCase):
    """Admin users should also be able to access the protected endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api:protected")
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass123"
        )
        self.client.force_authenticate(user=self.admin)

    def test_admin_authenticated_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_response_user_matches(self):
        response = self.client.get(self.url)
        self.assertIn("admin", response.data["user"])
