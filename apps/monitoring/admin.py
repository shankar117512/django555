# apps/monitoring/admin.py
from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__username", "action")
