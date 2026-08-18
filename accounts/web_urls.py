# accounts/web_urls.py

from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [

    path(
        "login/",
        views.web_login_view,
        name="login",
    ),

    path(
        "logout/",
        views.web_logout_view,
        name="logout",
    ),

]
