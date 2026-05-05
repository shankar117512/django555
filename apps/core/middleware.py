# apps/core/middleware.py
from django_tenants.middleware.main import TenantMainMiddleware


class TenantMiddlewareWithHealthCheck(TenantMainMiddleware):
    HEALTH_CHECK_PATH = "/health/"

    def process_request(self, request):
        if request.path == self.HEALTH_CHECK_PATH:
            return None  # skip tenant resolution entirely
        return super().process_request(request)
