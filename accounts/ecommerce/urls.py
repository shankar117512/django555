from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.ecommerce_login_view, name="ecommerce_login"),
    path("logout/", views.ecommerce_logout_view, name="ecommerce_logout"),
    path(
        "dashboard/",
        views.ecommerce_dashboard_view,
        name="ecommerce_dashboard",
    ),

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
