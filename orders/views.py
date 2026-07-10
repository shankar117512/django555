# orders/views.py
from rest_framework import generics, permissions

from .models import Client, Domain
from .serializers import ClientSerializer


class ClientListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/orders/clients/ — కొత్త tenant (company) create చేయడం"""

    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        client = serializer.save()
        Domain.objects.create(
            domain=f"{client.schema_name}.yourapp.com",
            tenant=client,
            is_primary=True,
        )


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAdminUser]
