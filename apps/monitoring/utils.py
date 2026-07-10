# apps/monitoring/utils.py
from .models import ActivityLog


def log_activity(user, action, request=None, metadata=None):
    """
    Record a user action (login, register, logout, etc.) in ActivityLog.
    `request` is accepted for future use (e.g. capturing IP/User-Agent)
    but not required.
    """
    ActivityLog.objects.create(
        user=user,
        action=action,
        metadata=metadata or {},
    )
