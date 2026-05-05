class TenantMiddlewareWithHealthCheck:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip tenant logic for health check endpoints
        if request.path in ("/health/", "/healthz/", "/ready/"):
            return self.get_response(request)

        # Your tenant resolution logic goes here
        # e.g., resolve tenant from request.get_host() or subdomain
        # request.tenant = ...

        response = self.get_response(request)
        return response
