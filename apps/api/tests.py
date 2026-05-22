# apps/api/tests.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class ProtectedViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("api:protected")
        self.user = User.objects.create_user(username="alice", password="secret123")

    # ── Authentication ────────────────────────────────────────────────────────

    def test_unauthenticated_get_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_message_field(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data["message"], "authenticated")

    def test_response_contains_correct_username(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data["user"], "alice")

    # ── Method enforcement ────────────────────────────────────────────────────

    def test_post_returns_405(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(
            self.client.post(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_put_returns_405(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(
            self.client.put(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_delete_returns_405(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(
            self.client.delete(self.url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
