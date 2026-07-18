from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import escape

from productos.models import Producto


SITEMAP_STATIC_ROUTES = [
    ('inicio', 'daily', '1.0'),
    ('catalogo', 'daily', '0.95'),
    ('disena_regalo', 'weekly', '0.9'),
    ('como_comprar', 'monthly', '0.8'),
    ('preguntas_frecuentes', 'monthly', '0.7'),
    ('terminos_condiciones', 'yearly', '0.4'),
    ('aviso_privacidad', 'yearly', '0.3'),
]


def _absolute_url(request, path):
    return request.build_absolute_uri(path)


def robots_txt(request):
    sitemap_url = _absolute_url(request, reverse('sitemap_xml'))
    content = '\n'.join(
        [
            'User-agent: *',
            'Allow: /',
            'Disallow: /admin/',
            'Disallow: /carrito/',
            '',
            f'Sitemap: {sitemap_url}',
            '',
        ]
    )
    return HttpResponse(content, content_type='text/plain; charset=utf-8')


def sitemap_xml(request):
    url_items = []

    for route_name, changefreq, priority in SITEMAP_STATIC_ROUTES:
        url_items.append(
            {
                'loc': _absolute_url(request, reverse(route_name)),
                'changefreq': changefreq,
                'priority': priority,
                'lastmod': '',
            }
        )

    productos = Producto.objects.filter(stock__gt=0).order_by('id').only('id', 'fecha_creacion')
    for producto in productos:
        url_items.append(
            {
                'loc': _absolute_url(request, reverse('detalle_producto', args=[producto.id])),
                'changefreq': 'weekly',
                'priority': '0.8',
                'lastmod': producto.fecha_creacion.date().isoformat() if producto.fecha_creacion else '',
            }
        )

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for item in url_items:
        lines.append('  <url>')
        lines.append(f'    <loc>{escape(item["loc"])}</loc>')
        if item['lastmod']:
            lines.append(f'    <lastmod>{item["lastmod"]}</lastmod>')
        lines.append(f'    <changefreq>{item["changefreq"]}</changefreq>')
        lines.append(f'    <priority>{item["priority"]}</priority>')
        lines.append('  </url>')
    lines.append('</urlset>')

    return HttpResponse('\n'.join(lines), content_type='application/xml; charset=utf-8')


def custom_404(request, exception):
    return render(request, "404.html", status=404)
