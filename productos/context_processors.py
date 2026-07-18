from django.db.models import Count

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


def categorias_menu(request):
    categorias = (
        Categoria.objects.annotate(total_productos=Count('producto'))
        .filter(total_productos__gt=0)
        .order_by('nombre')
    )
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
    return {"canonical_page_url": request.build_absolute_uri(request.path)}
