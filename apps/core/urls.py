# apps/core/urls.py
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # root "/" -> smart redirect (login or dashboard)
    path("", views.home_view, name="home"),

    path("client/dashboard/", views.dashboard_view, name="dashboard"),
    path("client/campaigns/", views.campaigns_view, name="campaigns"),
    path("client/leads/", views.leads_view, name="leads"),
    path("client/ai/", views.ai_insights_view, name="ai_insights"),
]
