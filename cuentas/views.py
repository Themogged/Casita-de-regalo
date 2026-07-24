from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from asistente.memory import get_memory_profile
from carrito.services import cart_snapshot, get_cart_for_request
from pedidos.models import Pedido

from .forms import (
    AccountAuthenticationForm,
    DirectPasswordChangeForm,
    ProfileForm,
    SignUpForm,
)


class AccountLoginView(LoginView):
    template_name = "cuentas/ingresar.html"
    authentication_form = AccountAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            self.request.session.set_expiry(0)
        return response


def change_password(request):
    current_user = request.user if request.user.is_authenticated else None
    form = DirectPasswordChangeForm(
        request.POST or None,
        request=request,
        user=current_user,
    )
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if current_user is not None:
            update_session_auth_hash(request, user)
        else:
            login(request, user)
        messages.success(request, "Tu contraseña se actualizó correctamente.")
        return redirect("account_profile")
    return render(request, "cuentas/cambiar_clave.html", {"form": form})


def signup(request):
    if request.user.is_authenticated:
        return redirect("account_profile")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            get_cart_for_request(request)
            get_memory_profile(user)
            messages.success(request, "Tu cuenta quedó lista.")
            return redirect("account_profile")
    else:
        form = SignUpForm()
    return render(request, "cuentas/registro.html", {"form": form})


@login_required
def profile(request):
    memory_profile = get_memory_profile(request.user)
    cart = get_cart_for_request(request)
    orders = Pedido.objects.filter(usuario=request.user).prefetch_related("items").order_by("-fecha")[:8]
    return render(
        request,
        "cuentas/perfil.html",
        {
            "profile_form": ProfileForm(instance=request.user),
            "memory_profile": memory_profile,
            "memory_count": request.user.assistant_memories.count(),
            "cart_snapshot": cart_snapshot(request, cart),
            "orders": orders,
        },
    )


@login_required
def update_profile(request):
    if request.method != "POST":
        return redirect("account_profile")
    form = ProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Perfil actualizado.")
    else:
        messages.error(request, "Revisa los datos del perfil.")
        memory_profile = get_memory_profile(request.user)
        cart = get_cart_for_request(request)
        orders = Pedido.objects.filter(usuario=request.user).prefetch_related("items").order_by("-fecha")[:8]
        return render(
            request,
            "cuentas/perfil.html",
            {
                "profile_form": form,
                "memory_profile": memory_profile,
                "memory_count": request.user.assistant_memories.count(),
                "cart_snapshot": cart_snapshot(request, cart),
                "orders": orders,
            },
            status=400,
        )
    return redirect(reverse("account_profile"))
