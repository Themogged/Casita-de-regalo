from .services import get_cart_for_request, mirror_cart_to_session


def carrito_total(request):
    try:
        cart = get_cart_for_request(request)
        total = sum(mirror_cart_to_session(request, cart).values())
    except Exception:
        # El encabezado debe seguir disponible durante una migración o mantenimiento.
        total = 0
    return {"carrito_total": total}
