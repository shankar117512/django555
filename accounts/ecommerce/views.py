from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import (
    CategoryForm,
    EcommerceLoginForm,
    EcommerceUserCreationForm,
    ProductForm,
)
from .models import Category, Order, Product


User = get_user_model()


def _ecommerce_staff_required(request):
    if not request.user.is_authenticated:
        return False

    return request.user.is_staff or request.user.is_superuser


def _redirect_if_not_staff(request):
    if not _ecommerce_staff_required(request):
        return redirect("accounts:ecommerce_login")

    return None


def ecommerce_login_view(request):
    if request.user.is_authenticated and _ecommerce_staff_required(request):
        return redirect("accounts:ecommerce_dashboard")

    form = EcommerceLoginForm(request.POST or None)
    error_message = ""

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            error_message = "Invalid username or password."
        elif not user.is_active:
            error_message = "This account is inactive."
        elif not (user.is_staff or user.is_superuser):
            error_message = (
                "This account does not have "
                "E-commerce dashboard access."
            )
        else:
            login(request, user)
            return redirect("accounts:ecommerce_dashboard")

    return render(
        request,
        "accounts/ecommerce/login.html",
        {
            "form": form,
            "error_message": error_message,
        },
    )


@login_required(login_url="/accounts/ecommerce/login/")
def ecommerce_logout_view(request):
    logout(request)
    return redirect("accounts:ecommerce_login")


@login_required(login_url="/accounts/ecommerce/login/")
def ecommerce_dashboard_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    total_products = Product.objects.count()
    active_products = Product.objects.filter(
        is_active=True
    ).count()

    total_categories = Category.objects.count()

    total_customers = User.objects.filter(
        is_staff=False,
        is_superuser=False,
    ).count()

    total_orders = Order.objects.count()

    pending_orders = Order.objects.filter(
        status=Order.STATUS_PENDING
    ).count()

    completed_orders = Order.objects.filter(
        status=Order.STATUS_DELIVERED
    ).count()

    total_revenue = (
        Order.objects.filter(
            status=Order.STATUS_DELIVERED
        ).aggregate(
            total=Sum("total_amount")
        )["total"]
        or Decimal("0.00")
    )

    low_stock_products = Product.objects.filter(
        stock__lte=5,
        is_active=True,
    ).order_by("stock", "name")[:8]

    recent_orders = (
        Order.objects.select_related("customer")
        .order_by("-created_at")[:8]
    )

    recent_products = (
        Product.objects.select_related("category")
        .order_by("-created_at")[:8]
    )

    context = {
        "total_products": total_products,
        "active_products": active_products,
        "total_categories": total_categories,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "total_revenue": total_revenue,
        "low_stock_products": low_stock_products,
        "recent_orders": recent_orders,
        "recent_products": recent_products,
    }

    return render(
        request,
        "accounts/ecommerce/dashboard.html",
        context,
    )


@login_required(login_url="/accounts/ecommerce/login/")
def product_list_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    search = request.GET.get("q", "").strip()

    products = Product.objects.select_related(
        "category"
    )

    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(sku__icontains=search)
            | Q(category__name__icontains=search)
        )

    return render(
        request,
        "accounts/ecommerce/products.html",
        {
            "products": products,
            "search": search,
        },
    )


@login_required(login_url="/accounts/ecommerce/login/")
@require_http_methods(["GET", "POST"])
def product_create_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    form = ProductForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Product created successfully.",
        )

        return redirect("accounts:ecommerce_products")

    return render(
        request,
        "accounts/ecommerce/product_form.html",
        {
            "form": form,
            "title": "Add Product",
            "button_text": "Create Product",
        },
    )


@login_required(login_url="/accounts/ecommerce/login/")
@require_http_methods(["GET", "POST"])
def product_edit_view(request, product_id):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    product = get_object_or_404(
        Product,
        pk=product_id,
    )

    form = ProductForm(
        request.POST or None,
        request.FILES or None,
        instance=product,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Product updated successfully.",
        )

        return redirect("accounts:ecommerce_products")

    return render(
        request,
        "accounts/ecommerce/product_form.html",
        {
            "form": form,
            "product": product,
            "title": "Edit Product",
            "button_text": "Update Product",
        },
    )


@login_required(login_url="/accounts/ecommerce/login/")
@require_http_methods(["POST"])
def product_delete_view(request, product_id):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    product = get_object_or_404(
        Product,
        pk=product_id,
    )

    product.delete()

    messages.success(
        request,
        "Product deleted successfully.",
    )

    return redirect("accounts:ecommerce_products")


@login_required(login_url="/accounts/ecommerce/login/")
def category_list_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    categories = Category.objects.annotate(
        product_count=Count("products")
    )

    return render(
        request,
        "accounts/ecommerce/categories.html",
        {"categories": categories},
    )


@login_required(login_url="/accounts/ecommerce/login/")
@require_http_methods(["GET", "POST"])
def category_create_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    form = CategoryForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Category created successfully.",
        )

        return redirect("accounts:ecommerce_categories")

    return render(
        request,
        "accounts/ecommerce/category_form.html",
        {
            "form": form,
            "title": "Add Category",
            "button_text": "Create Category",
        },
    )


@login_required(login_url="/accounts/ecommerce/login/")
def customer_list_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    customers = User.objects.filter(
        is_staff=False,
        is_superuser=False,
    ).order_by("-date_joined")

    return render(
        request,
        "accounts/ecommerce/customers.html",
        {"customers": customers},
    )


@login_required(login_url="/accounts/ecommerce/login/")
@require_http_methods(["GET", "POST"])
def customer_create_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    form = EcommerceUserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()

        messages.success(
            request,
            f"User '{user.username}' created successfully.",
        )

        return redirect("accounts:ecommerce_customers")

    return render(
        request,
        "accounts/ecommerce/customer_form.html",
        {
            "form": form,
            "title": "Create User",
            "button_text": "Create User",
        },
    )


@login_required(login_url="/accounts/ecommerce/login/")
def order_list_view(request):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    orders = Order.objects.select_related(
        "customer"
    ).order_by("-created_at")

    return render(
        request,
        "accounts/ecommerce/orders.html",
        {"orders": orders},
    )


@login_required(login_url="/accounts/ecommerce/login/")
def order_detail_view(request, order_id):
    redirect_response = _redirect_if_not_staff(request)

    if redirect_response:
        return redirect_response

    order = get_object_or_404(
        Order.objects.select_related("customer"),
        pk=order_id,
    )

    items = order.items.select_related("product")

    return render(
        request,
        "accounts/ecommerce/order_detail.html",
        {
            "order": order,
            "items": items,
        },
    )
