from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SchoolStudent, SchoolTeacher, User

from .ecommerce.models import Category, Order, OrderItem, Product


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

@admin.register(Category)
class EcommerceCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class EcommerceProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "price",
        "discount_price",
        "stock",
        "is_active",
        "is_featured",
    )
    list_filter = (
        "category",
        "is_active",
        "is_featured",
    )
    search_fields = (
        "name",
        "sku",
    )
    prepopulated_fields = {"slug": ("name",)}
    list_editable = (
        "price",
        "discount_price",
        "stock",
        "is_active",
    )


@admin.register(Order)
class EcommerceOrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "status",
        "total_amount",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "order_number",
        "customer__username",
        "customer__email",
    )
    readonly_fields = (
        "order_number",
        "created_at",
        "updated_at",
    )


@admin.register(OrderItem)
class EcommerceOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "unit_price",
        "subtotal",
    )
    search_fields = (
        "order__order_number",
        "product__name",
        "product__sku",
    )
