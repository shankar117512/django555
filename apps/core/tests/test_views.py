from unittest.mock import MagicMock, patch

from django.test import RequestFactory

from apps.core.middleware import TenantMiddlewareWithHealthCheck


class TestMiddleware:
    def get_middleware(self):
        get_response = MagicMock(return_value=MagicMock(status_code=200))
        return TenantMiddlewareWithHealthCheck(get_response)

    def test_health_check_path_skips_tenant_resolution(self):
        factory = RequestFactory()
        request = factory.get("/health/")
        middleware = self.get_middleware()
        result = middleware.process_request(request)
        assert result is None

    def test_non_health_check_path_calls_super(self):
        factory = RequestFactory()
        request = factory.get("/some-other-path/")
        middleware = self.get_middleware()
        with patch(
            "apps.core.middleware.TenantMainMiddleware.process_request",
            return_value=None,
        ) as mock_super:
            middleware.process_request(request)
            mock_super.assert_called_once_with(request)

    def test_health_check_path_constant(self):
        assert TenantMiddlewareWithHealthCheck.HEALTH_CHECK_PATH == "/health/"
