from django.apps import AppConfig


class EcommerceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts.ecommerce"
    label = "ecommerce"
    verbose_name = "E-Commerce"
