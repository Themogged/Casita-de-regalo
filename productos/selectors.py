from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Count, Q

from .models import Categoria, Producto, VideoElaboracion


CATALOG_ORDERINGS = {
    "destacados": ("-destacado", "nombre"),
    "precio_asc": ("precio", "nombre"),
    "precio_desc": ("-precio", "nombre"),
    "recientes": ("-fecha_creacion", "nombre"),
    "nombre": ("nombre",),
    "cumpleanos": ("-destacado", "nombre"),
    "aniversario": ("-destacado", "nombre"),
    "elaborados": ("-precio", "nombre"),
}

CATALOG_ORDER_OPTIONS = [
    ("destacados", "Destacados"),
    ("precio_asc", "Precio: menor a mayor"),
    ("precio_desc", "Precio: mayor a menor"),
    ("recientes", "Más recientes"),
    ("cumpleanos", "Recomendados para cumpleaños"),
    ("aniversario", "Recomendados para aniversario"),
    ("elaborados", "Más elaborados"),
    ("nombre", "Nombre"),
]

CATALOG_PRICE_OPTIONS = [
    ("", "Todos los presupuestos"),
    ("menos_80", "Menos de $80.000"),
    ("80_120", "$80.000 - $120.000"),
    ("120_170", "$120.000 - $170.000"),
    ("mas_170", "Más de $170.000"),
]

CATALOG_OCCASION_OPTIONS = [
    ("", "Todas las ocasiones"),
    ("cumpleanos", "Cumpleaños"),
    ("aniversario", "Aniversario"),
    ("amor", "Amor"),
    ("ninos", "Niños"),
    ("agradecimiento", "Agradecimiento"),
]

CATALOG_PERSON_OPTIONS = [
    ("", "Cualquier persona"),
    ("ella", "Para ella"),
    ("el", "Para él"),
    ("pareja", "Para pareja"),
    ("ninos", "Para niños"),
    ("mama", "Para mamá"),
]

CATALOG_TYPE_OPTIONS = [
    ("", "Todos los tipos"),
    ("desayuno", "Desayunos"),
    ("caja", "Cajas"),
    ("flores", "Flores"),
    ("mini", "Mini detalles"),
    ("tematico", "Temáticos"),
    ("snacks", "Snacks"),
]

CATALOG_TIME_OPTIONS = [
    ("", "Cualquier tiempo"),
    ("disponible", "Disponible para cotizar"),
    ("1_2", "Pedido con 1-2 días"),
]

CATALOG_ATTRIBUTE_OPTIONS = [
    ("flores", "Con flores"),
    ("peluche", "Con peluche"),
    ("globos", "Con globos"),
    ("desayuno", "Con desayuno"),
    ("frutas", "Con frutas"),
    ("luces", "Con luces"),
]

CATALOG_FILTER_LABELS = {
    value: label
    for options in [
        CATALOG_PRICE_OPTIONS,
        CATALOG_OCCASION_OPTIONS,
        CATALOG_PERSON_OPTIONS,
        CATALOG_TYPE_OPTIONS,
        CATALOG_TIME_OPTIONS,
        CATALOG_ATTRIBUTE_OPTIONS,
        CATALOG_ORDER_OPTIONS,
    ]
    for value, label in options
    if value
}

CATALOG_TOKEN_FILTERS = {
    "cumpleanos": ["cumple", "cumpleaños", "feliz día", "birthday"],
    "aniversario": ["aniversario", "meses", "pareja"],
    "amor": ["amor", "romántico", "romantico", "corazón", "corazon", "rosas"],
    "ninos": ["niño", "niños", "infantil", "personaje", "stitch", "toy story", "temático", "tematico"],
    "agradecimiento": ["gracias", "agradecimiento", "especial"],
    "ella": ["mujer", "ella", "mamá", "mama", "rosas", "flores"],
    "el": ["hombre", "hombres", "papá", "papa", "sobrio"],
    "pareja": ["pareja", "amor", "romántico", "romantico", "aniversario", "corazón", "corazon"],
    "mama": ["mamá", "mama", "madre"],
    "desayuno": ["desayuno", "waffle", "wafle", "wafles", "jugo", "milo", "bonyurt"],
    "caja": ["caja", "cajita", "acetato", "madera"],
    "flores": ["flor", "flores", "ramo", "rosas", "girasol"],
    "mini": ["mini", "pequeño", "pequeno"],
    "tematico": ["temático", "tematico", "personaje", "stitch", "toy story", "hello kitty"],
    "snacks": ["snack", "snacks", "chocolatina", "chocolate", "dulces", "cereal"],
    "peluche": ["peluche"],
    "globos": ["globo", "globos", "arco"],
    "frutas": ["fruta", "frutas", "fresas", "manzana", "pera"],
    "luces": ["luces", "luz"],
}


def _text_q(tokens):
    query = Q()
    for token in tokens:
        query |= (
            Q(nombre__icontains=token)
            | Q(descripcion__icontains=token)
            | Q(categoria__nombre__icontains=token)
        )
    return query


def _expanded_search_terms(search):
    terms = [search]
    normalized = search.lower()
    if "cumpleanos" in normalized:
        terms.extend(["cumpleaños", "cumple"])
    if "hombre" in normalized:
        terms.extend(["hombre", "hombres", "para hombres"])
    if "nino" in normalized or "niño" in normalized:
        terms.extend(["niño", "niños", "infantil"])
    if "desayuno" in normalized:
        terms.extend(CATALOG_TOKEN_FILTERS["desayuno"])
    if "rosa" in normalized:
        terms.extend(["rosas", "flores"])
    return list(dict.fromkeys(filter(None, terms)))


def _price_from_search(search):
    normalized = search.lower().replace(".", "").replace(",", "")
    digits = "".join(character if character.isdigit() else " " for character in normalized).split()
    if not digits:
        return None

    amount = Decimal(digits[0])
    if amount < 1000:
        amount *= 1000

    if "menos" in normalized or "hasta" in normalized:
        return "lte", amount
    if "mas de" in normalized or "más de" in normalized or "mayor" in normalized:
        return "gte", amount
    return None


def _is_price_only_search(search):
    normalized = search.lower().replace(".", "").replace(",", "")
    for word in ["menos", "hasta", "mas", "más", "mayor", "de", "mil", "pesos", "cop"]:
        normalized = normalized.replace(word, " ")
    normalized = "".join(" " if character.isdigit() else character for character in normalized)
    return not normalized.strip()


def _apply_price_filter(products, price_range):
    if price_range == "menos_80":
        return products.filter(precio__lt=Decimal("80000"))
    if price_range == "80_120":
        return products.filter(precio__gte=Decimal("80000"), precio__lte=Decimal("120000"))
    if price_range == "120_170":
        return products.filter(precio__gt=Decimal("120000"), precio__lte=Decimal("170000"))
    if price_range == "mas_170":
        return products.filter(precio__gt=Decimal("170000"))
    return products


def get_categories_with_products():
    return (
        Categoria.objects.annotate(total_productos=Count("producto"))
        .filter(total_productos__gt=0)
        .order_by("nombre")
    )


def get_catalog_queryset(
    search="",
    category_id="",
    order="destacados",
    price_range="",
    occasion="",
    person="",
    product_type="",
    time_filter="",
    attributes=None,
):
    products = Producto.objects.select_related("categoria").all()
    categories = get_categories_with_products()
    current_category = None
    attributes = attributes or []

    if search:
        parsed_price = _price_from_search(search)
        if not parsed_price or not _is_price_only_search(search):
            products = products.filter(_text_q(_expanded_search_terms(search)))
        if parsed_price:
            operator, amount = parsed_price
            if operator == "lte":
                products = products.filter(precio__lte=amount)
            elif operator == "gte":
                products = products.filter(precio__gte=amount)

    if str(category_id).isdigit():
        current_category = categories.filter(id=int(category_id)).first()
        if current_category:
            products = products.filter(categoria=current_category)

    products = _apply_price_filter(products, price_range)

    for filter_value in [occasion, person, product_type]:
        tokens = CATALOG_TOKEN_FILTERS.get(filter_value)
        if tokens:
            products = products.filter(_text_q(tokens))

    if time_filter in {"disponible", "1_2"}:
        products = products.filter(stock__gt=0)

    for attribute in attributes:
        tokens = CATALOG_TOKEN_FILTERS.get(attribute)
        if tokens:
            products = products.filter(_text_q(tokens))

    if order in {"cumpleanos", "aniversario"}:
        tokens = CATALOG_TOKEN_FILTERS[order]
        products = products.filter(_text_q(tokens))

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
