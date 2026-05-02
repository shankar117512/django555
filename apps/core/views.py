from django.http import HttpResponse


def home_view(request):
    return HttpResponse("Django dev Deployed was successfully", status=200)
