# apps/core/middleware.py
from django_tenants.middleware.main import TenantMainMiddleware

# Paths that must never block on tenant DB lookup
BYPASS_PREFIXES = ("/health/", "/monitoring/ping/")


class TenantMiddlewareWithHealthCheck(TenantMainMiddleware):
    # Class constant expected by tests
    HEALTH_CHECK_PATH = "/health/"

    def process_request(self, request):
        if any(request.path.startswith(p) for p in BYPASS_PREFIXES):
            return None  # skip tenant resolution entirely

        return super().process_request(request)
