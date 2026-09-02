from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # ============================================================
    # AUTHENTICATION
    # ============================================================
    path(
        "login/",
        views.ecommerce_login_view,
        name="ecommerce_login",
    ),
    path(
        "logout/",
        views.ecommerce_logout_view,
        name="ecommerce_logout",
    ),
    # ============================================================
    # PASSWORD RESET
    # ============================================================
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/ecommerce/password/password_reset_form.html",
            email_template_name="accounts/ecommerce/password/password_reset_email.html",
            subject_template_name="accounts/ecommerce/password/password_reset_subject.txt",
            success_url="/accounts/ecommerce/password-reset/done/",
        ),
        name="ecommerce_password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/ecommerce/password/password_reset_done.html",
        ),
        name="ecommerce_password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/ecommerce/password/password_reset_confirm.html",
            success_url="/accounts/ecommerce/reset/complete/",
        ),
        name="ecommerce_password_reset_confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/ecommerce/password/password_reset_complete.html",
        ),
        name="ecommerce_password_reset_complete",
    ),
    # ============================================================
    # DASHBOARD
    # ============================================================
    path(
        "dashboard/",
        views.ecommerce_dashboard_view,
        name="ecommerce_dashboard",
    ),
    # ============================================================
    # PRODUCTS
    # ============================================================
    path(
        "products/",
        views.product_list_view,
        name="ecommerce_products",
    ),
    path(
        "products/add/",
        views.product_create_view,
        name="ecommerce_product_create",
    ),
    path(
        "products/<int:product_id>/edit/",
        views.product_edit_view,
        name="ecommerce_product_edit",
    ),
    path(
        "products/<int:product_id>/delete/",
        views.product_delete_view,
        name="ecommerce_product_delete",
    ),
    # ============================================================
    # CATEGORIES
    # ============================================================
    path(
        "categories/",
        views.category_list_view,
        name="ecommerce_categories",
    ),
    path(
        "categories/add/",
        views.category_create_view,
        name="ecommerce_category_create",
    ),
    # ============================================================
    # CUSTOMERS
    # ============================================================
    path(
        "customers/",
        views.customer_list_view,
        name="ecommerce_customers",
    ),
    path(
        "customers/add/",
        views.customer_create_view,
        name="ecommerce_customer_create",
    ),
    # ============================================================
    # ORDERS
    # ============================================================
    path(
        "orders/",
        views.order_list_view,
        name="ecommerce_orders",
    ),
    path(
        "orders/<int:order_id>/",
        views.order_detail_view,
        name="ecommerce_order_detail",
    ),
]
