from django.core.paginator import Paginator
from django.db.models import Count, Q

from .models import Categoria, Producto, VideoElaboracion


CATALOG_ORDERINGS = {
    "destacados": ("-destacado", "nombre"),
    "precio_asc": ("precio", "nombre"),
    "precio_desc": ("-precio", "nombre"),
    "recientes": ("-fecha_creacion", "nombre"),
    "nombre": ("nombre",),
}

CATALOG_ORDER_OPTIONS = [
    ("destacados", "Destacados"),
    ("precio_asc", "Precio: menor a mayor"),
    ("precio_desc", "Precio: mayor a menor"),
    ("recientes", "Más recientes"),
    ("nombre", "Nombre"),
]


def get_categories_with_products():
    return (
        Categoria.objects.annotate(total_productos=Count("producto"))
        .filter(total_productos__gt=0)
        .order_by("nombre")
    )


def get_catalog_queryset(search="", category_id="", order="destacados"):
    products = Producto.objects.select_related("categoria").all()
    categories = get_categories_with_products()
    current_category = None

    if search:
        products = products.filter(
            Q(nombre__icontains=search)
            | Q(descripcion__icontains=search)
            | Q(categoria__nombre__icontains=search)
        )

    if str(category_id).isdigit():
        current_category = categories.filter(id=int(category_id)).first()
        if current_category:
            products = products.filter(categoria=current_category)

    ordering = CATALOG_ORDERINGS.get(order, CATALOG_ORDERINGS["destacados"])
    return products.order_by(*ordering), categories, current_category


def get_featured_products(base_queryset, search="", current_category=None, limit=6):
    if search or current_category:
        featured = list(base_queryset.filter(destacado=True)[:limit])
        return featured or list(base_queryset[:limit])

    featured = list(
        Producto.objects.select_related("categoria")
        .filter(destacado=True)
        .order_by("-destacado", "nombre")[:limit]
    )
    if featured:
        return featured

    return list(
        Producto.objects.select_related("categoria")
        .order_by("-destacado", "nombre")[:limit]
    )


def paginate_products(queryset, page_number, per_page=9):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)


def get_active_process_videos(limit=4):
    return VideoElaboracion.objects.filter(activo=True)[:limit]
