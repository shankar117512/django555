from django.test import RequestFactory


class TestMiddleware:
    def test_middleware_processes_request(self):
        factory = RequestFactory()
        request = factory.get("/")
        # test your middleware logic here
        assert request is not None
