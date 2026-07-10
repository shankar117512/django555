# orders/urls.py
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("clients/", views.ClientListCreateView.as_view(), name="client_list_create"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client_detail"),
]
