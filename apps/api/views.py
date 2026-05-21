# apps/api/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ProtectedView(APIView):
    """
    GET-only endpoint that requires a logged-in user.
    Returns {"message": "authenticated", "user": "<username>"}.
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]  # POST/PUT/DELETE → 405

    def get(self, request):
        return Response(
            {
                "message": "authenticated",
                "user": request.user.username,
            }
        )
