# apps/api/urls.py
from django.urls import path

from .views import APIRootView

urlpatterns = [
    path("v1/", APIRootView.as_view()),
]
