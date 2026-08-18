# accounts/web_urls.py

from django.urls import path

from . import views

app_name = "accounts"


urlpatterns = [
    # ========================================================
    # EXISTING BROWSER LOGIN
    # ========================================================
    path(
        "login/",
        views.web_login_view,
        name="login",
    ),
    path(
        "logout/",
        views.web_logout_view,
        name="logout",
    ),
    # ========================================================
    # SCHOOL MANAGEMENT SYSTEM
    # ========================================================
    path(
        "school/login/",
        views.school_login_view,
        name="school_login",
    ),
    path(
        "school/",
        views.school_teacher_list_view,
        name="school_home",
    ),
    path(
        "school/teacher-list/",
        views.school_teacher_list_view,
        name="school_teacher_list",
    ),
    path(
        "school/logout/",
        views.school_logout_view,
        name="school_logout",
    ),
]
