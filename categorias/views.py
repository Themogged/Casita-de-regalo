from django.shortcuts import redirect
from django.urls import reverse


def productos_por_categoria(request, categoria_id):
    return redirect(f"{reverse('inicio')}?categoria={categoria_id}")
