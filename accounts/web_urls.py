from django.urls import include, path

from . import views

app_name = "accounts"


urlpatterns = [
    # ============================================================
    # NORMAL WEBSITE LOGIN
    # ============================================================
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
    # ============================================================
    # SCHOOL MANAGEMENT SYSTEM
    # ============================================================
    path(
        "school/login/",
        views.school_login_view,
        name="school_login",
    ),
    path(
        "school/logout/",
        views.school_logout_view,
        name="school_logout",
    ),
    path(
        "school/dashboard/",
        views.school_dashboard_view,
        name="school_dashboard",
    ),
    # ============================================================
    # STUDENTS
    # ============================================================
    path(
        "school/student-list/",
        views.school_student_list_view,
        name="school_student_list",
    ),
    path(
        "school/student/<int:student_id>/",
        views.school_student_detail_view,
        name="school_student_detail",
    ),
    # ============================================================
    # TEACHERS
    # ============================================================
    path(
        "school/teacher-list/",
        views.school_teacher_list_view,
        name="school_teacher_list",
    ),
    path(
        "school/teacher/<int:teacher_id>/",
        views.school_teacher_detail_view,
        name="school_teacher_detail",
    ),
    path(
        "school/teacher/create/",
        views.school_teacher_create_view,
        name="school_teacher_create",
    ),
    # ============================================================
    # E-COMMERCE MANAGEMENT SYSTEM
    # ============================================================
    path(
        "ecommerce/",
        include("accounts.ecommerce.urls"),
    ),
]
