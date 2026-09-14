from django.shortcuts import redirect
from django.urls import reverse


def productos_por_categoria(request, categoria_id):
    return redirect(f"{reverse('catalogo')}?categoria={categoria_id}#catalogo")
