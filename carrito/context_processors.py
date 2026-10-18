from django.db import DatabaseError

from .services import cart_units_for_request


def carrito_total(request):
    try:
        total = cart_units_for_request(request)
    except DatabaseError:
        # El encabezado debe seguir disponible durante una migración o mantenimiento.
        total = 0
    return {"carrito_total": total}
