# accounts/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"


urlpatterns = [
    # ============================================================
    # API
    # ============================================================
    path(
        "register/",
        views.RegisterView.as_view(),
        name="register",
    ),
    path(
        "login/",
        views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "me/",
        views.MeView.as_view(),
        name="me",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    # ============================================================
    # NORMAL WEBSITE LOGIN
    # ============================================================
    path(
        "web-login/",
        views.web_login_view,
        name="web_login",
    ),
    path(
        "web-logout/",
        views.web_logout_view,
        name="web_logout",
    ),
    # ============================================================
    # SCHOOL MANAGEMENT SYSTEM
    # ============================================================
    # School login
    path(
        "school/login/",
        views.school_login_view,
        name="school_login",
    ),
    # School logout
    path(
        "school/logout/",
        views.school_logout_view,
        name="school_logout",
    ),
    # Dashboard
    path(
        "school/dashboard/",
        views.school_dashboard_view,
        name="school_dashboard",
    ),
    # ============================================================
    # STUDENTS
    # ============================================================
    # Students list
    path(
        "school/student-list/",
        views.school_student_list_view,
        name="school_student_list",
    ),
    # Student details
    path(
        "school/student/<int:student_id>/",
        views.school_student_detail_view,
        name="school_student_detail",
    ),
    # ============================================================
    # TEACHERS
    # ============================================================
    # Teachers list
    path(
        "school/teacher-list/",
        views.school_teacher_list_view,
        name="school_teacher_list",
    ),
    # Teacher details
    path(
        "school/teacher/<int:teacher_id>/",
        views.school_teacher_detail_view,
        name="school_teacher_detail",
    ),
    # Create teacher
    path(
        "school/teacher/create/",
        views.school_teacher_create_view,
        name="school_teacher_create",
    ),
]
