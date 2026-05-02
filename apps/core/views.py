from django.http import HttpResponse


def home(request):
    return HttpResponse("Django dev Deployed was successfully", status=200)
