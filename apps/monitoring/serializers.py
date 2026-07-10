# apps/monitoring/serializers.py
from rest_framework import serializers

from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = ActivityLog
        fields = ("id", "user", "action", "metadata", "created_at")


class DashboardMetricsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    total_clients = serializers.IntegerField()
    recent_activity = ActivityLogSerializer(many=True)
