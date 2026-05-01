from django.http import HttpResponse


def home(request):
    return HttpResponse("Django dev environment deployed was successfully!...")
