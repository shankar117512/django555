# apps/api/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class APIRootView(APIView):
    permission_classes = [IsAuthenticated]  # ← causes 401/403 for unauthenticated

    def get(self, request):
        return Response({"message": "API v1 root"})
