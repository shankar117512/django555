# apps/core/middleware.py
from django_tenants.middleware.main import TenantMainMiddleware

BYPASS_PREFIXES = ("/health/", "/monitoring/ping/")


class TenantMiddlewareWithHealthCheck(TenantMainMiddleware):
    def process_request(self, request):
        if any(request.path.startswith(p) for p in BYPASS_PREFIXES):
            request.tenant = None
            return None

        return super().process_request(request)
