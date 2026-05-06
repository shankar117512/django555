# apps/core/middleware.py
from django_tenants.middleware.main import TenantMainMiddleware

BYPASS_PATHS = ("/health/", "/health", "/metrics/", "/metrics")


class TenantMiddlewareWithHealthCheck(TenantMainMiddleware):
    def process_request(self, request):
        # Let health/metrics pass through without tenant resolution
        if request.path in BYPASS_PATHS:
            return None  # skip tenant lookup entirely
        return super().process_request(request)
