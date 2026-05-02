from django.http import HttpResponse


def home_view(request):
    """
    Public home endpoint. Returns 200 with success message.
    """
    html = """
    <!DOCTYPE html>
    <html>
      <head><title>Django App</title></head>
      <body>
        <h1>Django dev environment deployed successfully!</h1>
        <p>Welcome. The API is available at <a href="/api/">/api/</a></p>
        <p>Health check: <a href="/health/">/health/</a></p>
      </body>
    </html>
    """
    return HttpResponse(html)
