from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .seo_views import robots_txt, sitemap_xml
from .telemetry_views import collect_event


handler404 = "tienda_regalos.seo_views.custom_404"


admin.site.site_header = "Casita de Regalos"
admin.site.site_title = "Casita de Regalos"
admin.site.index_title = "Panel de gestión"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
    path("eventos/", collect_event, name="collect_event"),
    path("", include("productos.urls")),
    path("categoria/", include("categorias.urls")),
    path("carrito/", include("carrito.urls")),
    path("cuenta/memoria/", include("asistente.urls")),
    path("cuenta/", include("cuentas.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
