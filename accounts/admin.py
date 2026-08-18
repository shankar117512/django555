from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SchoolStudent, SchoolTeacher, User


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

    list_filter = (
        "is_staff",
        "is_active",
        "is_verified",
    )

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Extra Info",
            {
                "fields": (
                    "phone_number",
                    "is_verified",
                    "avatar",
                    "last_login_ip",
                )
            },
        ),
    )


@admin.register(SchoolStudent)
class SchoolStudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "name",
        "student_class",
        "joining_date",
        "email",
    )

    list_filter = (
        "student_class",
        "joining_date",
    )

    search_fields = (
        "student_id",
        "name",
        "email",
    )

    ordering = ("name",)


@admin.register(SchoolTeacher)
class SchoolTeacherAdmin(admin.ModelAdmin):
    list_display = (
        "teacher_id",
        "name",
        "email",
        "department",
        "subject",
        "joining_date",
    )

    list_filter = (
        "department",
        "subject",
        "joining_date",
    )

    search_fields = (
        "teacher_id",
        "name",
        "email",
        "department",
        "subject",
    )

    ordering = ("name",)
