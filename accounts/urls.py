# wassel-backend/accounts/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path("login/",               api.login_view,           name="login"),
    path("register/client/",     api.register_client,      name="register-client"),
    path("register/restaurant/", api.register_restaurant,  name="register-restaurant"),
    path("register/livreur/",    api.register_livreur,     name="register-livreur"),
    path("logout/",              api.logout_view,          name="logout"),
    path("change-password/",     api.change_password_view, name="change-password"),
    path("me/",                  api.me_view,              name="me"),
]
