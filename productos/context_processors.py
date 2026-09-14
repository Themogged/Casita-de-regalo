from django.core.cache import cache
from urllib.parse import urlencode
from django.db.models import Count
from django.templatetags.static import static

from .models import Categoria
from .whatsapp import (
    CATEGORY_INFO_MESSAGE,
    COVERAGE_INFO_MESSAGE,
    DEFAULT_ASSISTANCE_MESSAGE,
    GENERAL_INFO_MESSAGE,
    PAYMENT_DATA_MESSAGE,
    PERSONALIZATION_MESSAGE,
    build_whatsapp_url,
)

CATEGORIES_MENU_CACHE_KEY = "productos:categorias-menu:v2"
CATEGORIES_MENU_CACHE_SECONDS = 300


def categorias_menu(request):
    categorias = cache.get(CATEGORIES_MENU_CACHE_KEY)
    if categorias is None:
        categorias = list(
            Categoria.objects.annotate(total_productos=Count('producto'))
            .filter(
                total_productos__gt=0,
            )
            .order_by('nombre')
            .values('id', 'nombre')
        )
        infantil_preferida = None
        for nombre_preferido in ("Temáticos e infantiles", "Tematicos e infantiles", "Niños"):
            for categoria in categorias:
                if categoria["nombre"] == nombre_preferido:
                    infantil_preferida = categoria
                    break
            if infantil_preferida:
                break

        if infantil_preferida:
            categorias = [
                categoria
                for categoria in categorias
                if categoria["nombre"] not in {"Niños", "Temáticos e infantiles", "Tematicos e infantiles"}
            ]
            categorias.append(infantil_preferida)

        cache.set(CATEGORIES_MENU_CACHE_KEY, categorias, CATEGORIES_MENU_CACHE_SECONDS)

    return {'categorias_menu': categorias}


def business_links(request):
    return {
        'whatsapp_assistance_url': build_whatsapp_url(DEFAULT_ASSISTANCE_MESSAGE),
        'whatsapp_general_info_url': build_whatsapp_url(GENERAL_INFO_MESSAGE),
        'whatsapp_payment_url': build_whatsapp_url(PAYMENT_DATA_MESSAGE),
        'whatsapp_category_info_url': build_whatsapp_url(CATEGORY_INFO_MESSAGE),
        'whatsapp_personalization_url': build_whatsapp_url(PERSONALIZATION_MESSAGE),
        'whatsapp_coverage_url': build_whatsapp_url(COVERAGE_INFO_MESSAGE),
    }


def seo_context(request):
    canonical = request.build_absolute_uri(request.path)
    pagination = {}
    if request.path == "/catalogo/":
        for key in ("categoria", "page"):
            value = request.GET.get(key, "")
            if value.isdecimal() and len(value) <= 18 and int(value) > 0:
                pagination[key] = str(int(value))
    if pagination:
        canonical += "?" + urlencode(pagination)
    private = request.path.startswith(("/cuenta/", "/carrito/", "/admin/", "/pedidos/"))
    return {
        "canonical_page_url": canonical,
        "default_og_image_url": request.build_absolute_uri(static("productos/img/brand-casita-icon-512.png")),
        "robots_policy": "noindex, follow" if private or request.GET.get("q") else "index, follow",
    }
