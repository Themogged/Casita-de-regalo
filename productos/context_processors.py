from django.db.models import Count

from .models import Categoria


def categorias_menu(request):
    categorias = (
        Categoria.objects.annotate(total_productos=Count('producto'))
        .filter(total_productos__gt=0)
        .order_by('nombre')
    )
    return {'categorias_menu': categorias}
