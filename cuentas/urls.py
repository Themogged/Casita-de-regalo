from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.profile, name="account_profile"),
    path("actualizar/", views.update_profile, name="account_update"),
    path("crear/", views.signup, name="account_signup"),
    path(
        "ingresar/",
        views.AccountLoginView.as_view(),
        name="login",
    ),
    path(
        "cambiar-clave/",
        views.change_password,
        name="password_change",
    ),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
]
