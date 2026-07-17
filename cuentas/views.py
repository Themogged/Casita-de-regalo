from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from asistente.memory import get_memory_profile
from carrito.services import cart_snapshot, get_cart_for_request
from pedidos.models import Pedido

from .forms import ProfileForm, SignUpForm


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
