# apps/core/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def home_view(request):
    """
    Public home page.

    GET requests render the public home page.
    POST and other HTTP methods are rejected with 405.
    """
    return render(request, "core/home.html")


@login_required(login_url="accounts:login")
def dashboard_view(request):
    """
    Revenue Overview screen.

    TODO: replace the zeros below with real aggregates, e.g.:
        from apps.core.models import Campaign, Lead
        spend = Campaign.objects.aggregate(total=Sum("spend"))["total"] or 0
    """
    context = {
        "spend": 0,
        "leads_count": 0,
        "conversions": 0,
        "roi": 0.0,
        "funnel_labels": [
            "New",
            "Contacted",
            "Qualified",
            "Converted",
        ],
        "funnel_values": [0, 0, 0, 0],
        "active": "dashboard",
    }

    return render(request, "core/dashboard.html", context)


@login_required(login_url="accounts:login")
def campaigns_view(request):
    """
    Campaign Command Center.

    TODO: swap the empty list for a real queryset, e.g.:
        campaigns = Campaign.objects.select_related("client").all()
    """
    campaigns = []

    return render(
        request,
        "core/campaigns.html",
        {
            "campaigns": campaigns,
            "active": "campaigns",
        },
    )


@login_required(login_url="accounts:login")
def leads_view(request):
    """
    Lead Funnel screen.

    TODO: replace with real counts, e.g.:
        new = Lead.objects.filter(stage="new").count()
    """
    context = {
        "new_count": 0,
        "qualified_count": 0,
        "converted_count": 0,
        "active": "leads",
    }

    return render(request, "core/leads.html", context)


@login_required(login_url="accounts:login")
def ai_insights_view(request):
    """
    AI Lead Insights screen.

    TODO: hook this up to your AI scoring/prediction service
    and pass a list of recommendation dictionaries as `insights`.
    """
    insights = []

    return render(
        request,
        "core/ai_insights.html",
        {
            "insights": insights,
            "active": "ai",
        },
    )
