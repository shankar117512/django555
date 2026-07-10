# orders/admin.py
from django.contrib import admin

from .models import Client, Domain


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("schema_name", "name", "paid_until", "on_trial", "created_on")
    search_fields = ("schema_name", "name")
    list_filter = ("on_trial",)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    search_fields = ("domain",)
