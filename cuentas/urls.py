from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.profile, name="account_profile"),
    path("actualizar/", views.update_profile, name="account_update"),
    path("crear/", views.signup, name="account_signup"),
    path(
        "ingresar/",
        auth_views.LoginView.as_view(template_name="cuentas/ingresar.html"),
        name="login",
    ),
    path(
        "recuperar/",
        views.ReliablePasswordResetView.as_view(
            template_name="cuentas/recuperar.html",
            email_template_name="cuentas/correo_recuperacion.txt",
            subject_template_name="cuentas/asunto_recuperacion.txt",
        ),
        name="password_reset",
    ),
    path(
        "recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="cuentas/recuperar_enviado.html"
        ),
        name="password_reset_done",
    ),
    path(
        "recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="cuentas/recuperar_confirmar.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="cuentas/recuperar_listo.html"
        ),
        name="password_reset_complete",
    ),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
]
