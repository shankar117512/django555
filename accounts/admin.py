# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "is_verified",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = ("is_staff", "is_active", "is_verified")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Extra Info",
            {"fields": ("phone_number", "is_verified", "avatar", "last_login_ip")},
        ),
    )
