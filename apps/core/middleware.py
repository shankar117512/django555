# apps/core/middleware.py
from django_tenants.middleware.main import TenantMainMiddleware


class TenantMiddlewareWithHealthCheck(TenantMainMiddleware):
    def process_request(self, request):
        if request.path.startswith("/health/"):
            return None  # skip tenant resolution

        return super().process_request(request)
