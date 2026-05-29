import json
import os
import shutil
from io import StringIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image
from unittest import mock

from .admin import CategoriaAdmin, GaleriaProductoFilter, ImagenProductoFilter, ProductoAdmin, VideoElaboracionAdmin
from .image_frames import generate_yellow_child_frame, slugify_filename
from .models import Categoria, Producto, ProductoImagen, VideoElaboracion
from .whatsapp import build_whatsapp_url


class ProductFrameTests(SimpleTestCase):
    def test_slugify_filename_normaliza_nombre_de_producto(self):
        self.assertEqual(
            slugify_filename('Caja Stitch cumpleaños deluxe'),
            'caja-stitch-cumpleanos-deluxe',
        )

    def test_generate_yellow_child_frame_crea_webp_vertical(self):
        temp_path = Path('.tmp-test-media') / 'product-frame'
        if temp_path.exists():
            shutil.rmtree(temp_path)
        temp_path.mkdir(parents=True)
        try:
            source_path = temp_path / 'producto.jpg'
            logo_path = temp_path / 'logo.webp'
            output_path = temp_path / 'producto-marco.webp'

            Image.new('RGB', (420, 300), (40, 150, 220)).save(source_path)
            Image.new('RGBA', (90, 90), (255, 255, 255, 0)).save(logo_path)

            result = generate_yellow_child_frame(
                source_path,
                logo_path,
                output_path,
                'Producto infantil',
            )

            self.assertEqual(result, output_path)
            self.assertTrue(output_path.exists())
            with Image.open(output_path) as generated:
                self.assertEqual(generated.size, (1080, 1350))
                self.assertEqual(generated.format, 'WEBP')
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)


class WhatsappUrlTests(TestCase):
    @override_settings(BUSINESS_WHATSAPP_NUMBER='570000000000')
    def test_build_whatsapp_url_usa_numero_configurado_y_codifica_mensaje(self):
        url = build_whatsapp_url('Hola, quiero asesoría para una ocasión especial.')
        parsed = urlparse(url)

        self.assertEqual(parsed.netloc, 'wa.me')
        self.assertEqual(parsed.path, '/570000000000')
        self.assertEqual(
            parse_qs(parsed.query)['text'][0],
            'Hola, quiero asesoría para una ocasión especial.',
        )


class CatalogoAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.categoria = Categoria.objects.create(nombre='Regalos')
        self.producto = Producto.objects.create(
            nombre='Caja sorpresa',
            descripcion='Detalle personalizado',
            precio='45000.00',
            stock=8,
            categoria=self.categoria,
            destacado=True,
            imagen='productos/caja-sorpresa.jpeg',
        )

    def test_producto_admin_exporta_productos_a_csv(self):
        producto_admin = ProductoAdmin(Producto, self.site)

        response = producto_admin.exportar_productos_csv(
            None,
            Producto.objects.filter(pk=self.producto.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8')
        self.assertIn('Caja sorpresa', content)
        self.assertIn('Regalos', content)
        self.assertIn('Estado', content)
        self.assertIn('Imagen principal', content)
        self.assertIn('Imagenes galeria', content)
        self.assertIn('disponible', content)

    def test_categoria_admin_muestra_resumen_operativo(self):
        Producto.objects.create(
            nombre='Detalle agotado',
            descripcion='Sin stock',
            precio='22000.00',
            stock=0,
            categoria=self.categoria,
        )
        categoria_admin = CategoriaAdmin(Categoria, self.site)

        categoria = categoria_admin.get_queryset(None).get(pk=self.categoria.pk)

        self.assertIn('casita-admin-count', str(categoria_admin.total_productos(categoria)))
        self.assertIn('is-success', str(categoria_admin.productos_disponibles(categoria)))
        self.assertIn('is-danger', str(categoria_admin.productos_agotados(categoria)))

    def test_producto_admin_muestra_estado_y_galeria_con_badges(self):
        ProductoImagen.objects.create(
            producto=self.producto,
            imagen='productos/galeria/caja-extra.jpeg',
            titulo='Detalle lateral',
        )
        producto_admin = ProductoAdmin(Producto, self.site)

        producto = producto_admin.get_queryset(None).get(pk=self.producto.pk)

        self.assertIn('casita-admin-badge is-success', str(producto_admin.estado_publico(producto)))
        self.assertIn('Principal + 1', str(producto_admin.galeria_estado(producto)))

    def test_admin_incluye_enlaces_publicos_de_catalogo(self):
        producto_admin = ProductoAdmin(Producto, self.site)
        categoria_admin = CategoriaAdmin(Categoria, self.site)

        self.assertIn(
            reverse('detalle_producto', args=[self.producto.pk]),
            str(producto_admin.ver_en_tienda(self.producto)),
        )
        self.assertIn(
            f"{reverse('inicio')}?categoria={self.categoria.pk}#catalogo",
            str(categoria_admin.ver_catalogo(self.categoria)),
        )

    def test_admin_filtra_productos_sin_imagen(self):
        producto_sin_imagen = Producto.objects.create(
            nombre='Detalle sin foto',
            descripcion='Pendiente de imagen',
            precio='25000.00',
            stock=4,
            categoria=self.categoria,
        )
        producto_admin = ProductoAdmin(Producto, self.site)
        filtro = ImagenProductoFilter(
            None,
            {'imagen_estado': 'sin_imagen'},
            Producto,
            producto_admin,
        )
        filtro.value = mock.Mock(return_value='sin_imagen')

        resultados = filtro.queryset(None, Producto.objects.all())

        self.assertIn(producto_sin_imagen, resultados)
        self.assertNotIn(self.producto, resultados)

    def test_admin_filtra_productos_sin_galeria(self):
        ProductoImagen.objects.create(
            producto=self.producto,
            imagen='productos/galeria/caja-extra.jpeg',
            titulo='Detalle lateral',
        )
        producto_sin_galeria = Producto.objects.create(
            nombre='Detalle sin galeria',
            descripcion='Producto con imagen principal solamente',
            precio='28000.00',
            stock=5,
            categoria=self.categoria,
            imagen='productos/detalle-sin-galeria.jpeg',
        )
        producto_admin = ProductoAdmin(Producto, self.site)
        filtro = GaleriaProductoFilter(
            None,
            {'galeria_estado': 'sin_galeria'},
            Producto,
            producto_admin,
        )
        filtro.value = mock.Mock(return_value='sin_galeria')

        resultados = filtro.queryset(None, Producto.objects.all())

        self.assertIn(producto_sin_galeria, resultados)
        self.assertNotIn(self.producto, resultados)

    def test_video_admin_acciones_masivas(self):
        video = VideoElaboracion.objects.create(
            titulo='Armado de prueba',
            descripcion='Proceso',
            video='procesos/videos/prueba.mp4',
            activo=False,
            destacado=False,
        )
        video_admin = VideoElaboracionAdmin(VideoElaboracion, self.site)
        video_admin.message_user = mock.Mock()

        video_admin.activar_videos(None, VideoElaboracion.objects.filter(pk=video.pk))
        video_admin.marcar_destacados(None, VideoElaboracion.objects.filter(pk=video.pk))

        video.refresh_from_db()
        self.assertTrue(video.activo)
        self.assertTrue(video.destacado)
        self.assertIn('Activo', str(video_admin.estado_publicacion(video)))
        self.assertIn('MP4', str(video_admin.archivo_video(video)))


class CatalogoViewsTests(TestCase):
    @staticmethod
    def _gif_file(nombre):
        return SimpleUploadedFile(
            nombre,
            (
                b'GIF89a\x01\x00\x01\x00\x80\x00\x00'
                b'\x00\x00\x00\xff\xff\xff!\xf9\x04\x01'
                b'\x00\x00\x00\x00,\x00\x00\x00\x00\x01'
                b'\x00\x01\x00\x00\x02\x02D\x01\x00;'
            ),
            content_type='image/gif',
        )

    def setUp(self):
        self.categoria_regalos = Categoria.objects.create(nombre='Regalos')
        self.categoria_flores = Categoria.objects.create(nombre='Flores')

        self.producto_principal = Producto.objects.create(
            nombre='Caja sorpresa',
            descripcion='Caja con dulces y detalles personalizados.',
            precio='24.99',
            stock=5,
            categoria=self.categoria_regalos,
            destacado=True,
            imagen=self._gif_file('principal.gif'),
        )
        self.producto_agotado = Producto.objects.create(
            nombre='Ramo premium',
            descripcion='Arreglo floral para ocasiones especiales.',
            precio='39.50',
            stock=0,
            categoria=self.categoria_flores,
        )
        self.relacionado = Producto.objects.create(
            nombre='Kit cumpleañero',
            descripcion='Incluye globo, taza y tarjeta.',
            precio='18.00',
            stock=4,
            categoria=self.categoria_regalos,
        )
        self.producto_elaborado = Producto.objects.create(
            nombre='Caja grande con flores',
            descripcion='Caja con rosas, flores, globos y chocolates para una sorpresa elaborada.',
            precio='130000.00',
            stock=4,
            categoria=self.categoria_flores,
        )
        self.producto_hombre = Producto.objects.create(
            nombre='Detalle para hombre',
            descripcion='Detalle sobrio para hombres con snacks y bebida.',
            precio='90000.00',
            stock=4,
            categoria=self.categoria_regalos,
        )

        for indice in range(10):
            Producto.objects.create(
                nombre=f'Referencia extra {indice}',
                descripcion='Producto extra para paginación.',
                precio='10.00',
                stock=2,
                categoria=self.categoria_regalos,
            )

    def test_catalogo_muestra_busqueda_por_texto(self):
        response = self.client.get(reverse('inicio'), {'q': 'sorpresa'}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Caja sorpresa')
        self.assertNotContains(response, 'Ramo premium')

    def test_inicio_muestra_bloques_de_servicio(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bello, Antioquia')
        self.assertContains(response, 'Cómo comprar')
        self.assertContains(response, 'Medios de pago')
        self.assertContains(response, 'Elige el detalle ideal')
        self.assertContains(response, 'Buscar detalle')
        self.assertContains(response, 'Ordenar por')
        self.assertContains(response, 'Filtros rápidos para encontrar mejor')
        self.assertContains(response, 'Presupuesto')
        self.assertContains(response, 'Persona')
        self.assertContains(response, 'Arma tu regalo a medida en una vista dedicada')
        self.assertContains(response, reverse('disena_regalo'))
        self.assertContains(response, 'floating-designer')
        self.assertContains(response, 'aria-label="Armar regalo a medida"')
        self.assertNotContains(response, 'Beta sin API')
        self.assertNotContains(response, 'data-gift-designer')
        self.assertContains(response, 'Agregar a mi cotización')
        self.assertContains(response, 'Incluye base tipo caja y acabados decorativos a juego.')
        self.assertNotContains(response, 'Incluye una base según la referencia y acabados decorativos.')
        self.assertContains(response, 'hero-product-card')
        self.assertNotContains(response, 'data-track-click')
        self.assertNotContains(response, 'registrar_interaccion')
        self.assertNotContains(response, 'Premium floral')

    def test_disena_regalo_muestra_configurador_completo(self):
        response = self.client.get(reverse('disena_regalo'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Arma tu regalo a medida')
        self.assertContains(response, 'data-gift-designer')
        self.assertContains(response, 'Acabados especiales')
        self.assertContains(response, 'Empezar a crear mi regalo')
        self.assertContains(response, 'Enviar idea por WhatsApp')
        self.assertContains(response, 'Recomendada')
        self.assertContains(response, 'Más económica')
        self.assertContains(response, 'Ver más bases')
        self.assertContains(response, 'designer-gift-cta')
        self.assertNotContains(response, 'Beta sin API')

    @override_settings(BUSINESS_WHATSAPP_NUMBER='570000000000')
    def test_inicio_usa_numero_whatsapp_configurado(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://wa.me/570000000000')

    def test_inicio_muestra_videos_de_elaboracion_activos(self):
        VideoElaboracion.objects.create(
            titulo='Armado de detalle personalizado',
            descripcion='Proceso real de decoración y empaque.',
            video='procesos/videos/proceso.mp4',
            destacado=True,
        )
        VideoElaboracion.objects.create(
            titulo='Video oculto',
            descripcion='No debe aparecer si esta inactivo.',
            video='procesos/videos/oculto.mp4',
            activo=False,
        )

        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'process-video-card')
        self.assertContains(response, 'Armado de detalle personalizado')
        self.assertContains(response, '<video controls muted preload="metadata" playsinline')
        self.assertContains(response, 'type="video/mp4"')
        self.assertNotContains(response, 'Video oculto')

    def test_inicio_envia_headers_de_seguridad(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertIn('Permissions-Policy', response.headers)

    def test_paginas_legales_cargan_correctamente(self):
        como_comprar = self.client.get(reverse('como_comprar'), secure=True)
        terminos = self.client.get(reverse('terminos_condiciones'), secure=True)
        privacidad = self.client.get(reverse('aviso_privacidad'), secure=True)
        preguntas = self.client.get(reverse('preguntas_frecuentes'), secure=True)

        self.assertEqual(como_comprar.status_code, 200)
        self.assertContains(como_comprar, 'C&oacute;mo comprar')
        self.assertContains(como_comprar, 'HowTo')
        self.assertEqual(terminos.status_code, 200)
        self.assertContains(terminos, 'T&eacute;rminos y condiciones')
        self.assertEqual(privacidad.status_code, 200)
        self.assertContains(privacidad, 'Aviso de privacidad')
        self.assertEqual(preguntas.status_code, 200)
        self.assertContains(preguntas, 'Preguntas frecuentes')
        self.assertContains(preguntas, 'FAQPage')

    def test_sitemap_y_robots_exponen_urls_publicas(self):
        robots = self.client.get(reverse('robots_txt'), secure=True)
        sitemap = self.client.get(reverse('sitemap_xml'), secure=True)

        self.assertEqual(robots.status_code, 200)
        self.assertContains(robots, 'Sitemap:')
        self.assertContains(robots, '/sitemap.xml')
        self.assertContains(robots, 'Disallow: /admin/')

        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, '<urlset')
        self.assertContains(sitemap, reverse('inicio'))
        self.assertContains(sitemap, reverse('disena_regalo'))
        self.assertContains(sitemap, reverse('como_comprar'))
        self.assertContains(sitemap, reverse('preguntas_frecuentes'))
        self.assertContains(sitemap, reverse('detalle_producto', args=[self.producto_principal.id]))

    def test_catalogo_filtra_por_categoria(self):
        response = self.client.get(reverse('inicio'), {'categoria': self.categoria_flores.id}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ramo premium')
        self.assertNotContains(response, 'Caja sorpresa')
        self.assertNotContains(response, 'id="disena-tu-regalo" data-gift-designer')

    def test_catalogo_filtra_por_presupuesto_atributo_y_persona(self):
        response = self.client.get(
            reverse('inicio'),
            {'presupuesto': '120_170', 'atributos': ['flores']},
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Caja grande con flores')
        self.assertNotContains(
            response,
            f'<a href="{reverse("detalle_producto", args=[self.producto_principal.id])}" class="product-title-link">{self.producto_principal.nombre}</a>',
            html=True,
        )
        self.assertContains(response, '$120.000 - $170.000')
        self.assertContains(response, 'Con flores')

        response = self.client.get(reverse('inicio'), {'persona': 'el'}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detalle para hombre')
        self.assertNotContains(
            response,
            f'<a href="{reverse("detalle_producto", args=[self.producto_agotado.id])}" class="product-title-link">{self.producto_agotado.nombre}</a>',
            html=True,
        )

    def test_catalogo_interpreta_busqueda_por_presupuesto(self):
        response = self.client.get(reverse('inicio'), {'q': 'menos de 100 mil'}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Caja sorpresa')
        self.assertNotContains(
            response,
            f'<a href="{reverse("detalle_producto", args=[self.producto_elaborado.id])}" class="product-title-link">{self.producto_elaborado.nombre}</a>',
            html=True,
        )

    def test_detalle_producto_muestra_relacionados(self):
        response = self.client.get(reverse('detalle_producto', args=[self.producto_principal.id]), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Caja sorpresa')
        self.assertContains(response, 'Kit cumpleañero')
        self.assertContains(response, 'Siguiente')
        self.assertContains(response, reverse('detalle_producto', args=[self.relacionado.id]))
        self.assertContains(response, 'Tiempo recomendado')
        self.assertContains(response, 'Ideal para')
        self.assertContains(response, 'Puede variar')
        self.assertContains(response, 'Agregar a mi cotizaci&oacute;n')
        self.assertContains(response, 'Cotizar por WhatsApp')
        self.assertContains(response, '<meta property="og:type" content="product">', html=True)
        self.assertContains(response, '"@type": "Product"')
        self.assertContains(response, '"priceCurrency": "COP"')

    def test_detalle_producto_muestra_galeria_cuando_hay_varias_imagenes(self):
        ProductoImagen.objects.create(
            producto=self.producto_principal,
            imagen=self._gif_file('extra.gif'),
            titulo='Vista lateral',
            orden=1,
        )

        response = self.client.get(reverse('detalle_producto', args=[self.producto_principal.id]), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-gallery-thumb')
        self.assertContains(response, 'data-gallery-prev')
        self.assertContains(response, 'Vista lateral')

    def test_catalogo_marca_productos_agotados(self):
        response = self.client.get(reverse('inicio'), {'q': 'ramo'}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ramo premium')
        self.assertContains(response, 'Agotado')

    def test_catalogo_no_muestra_cantidades_de_stock(self):
        response = self.client.get(reverse('inicio'), {'q': 'sorpresa'}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Disponible')
        self.assertNotContains(response, '5 unidades')
        self.assertNotContains(response, 'Ultimas')

    def test_detalle_no_muestra_cantidad_de_stock(self):
        response = self.client.get(reverse('detalle_producto', args=[self.producto_principal.id]), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Disponible para pedido')
        self.assertNotContains(response, '5 unidades')

    def test_catalogo_permite_abrir_detalle_desde_el_nombre(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'<a href="{reverse("detalle_producto", args=[self.producto_principal.id])}" class="product-title-link">{self.producto_principal.nombre}</a>',
            html=True,
        )

    def test_catalogo_mantiene_anchor_en_paginacion_y_filtros(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '?page=2#catalogo')
        self.assertContains(
            response,
            f'{reverse("inicio")}?categoria={self.categoria_regalos.id}#catalogo',
        )
        self.assertContains(response, 'class="catalog-chip js-catalog-nav is-active"')

    def test_asistente_devuelve_fallback_si_no_hay_api_key(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            response = self.client.post(
                reverse('assistant_chat'),
                data=json.dumps(
                    {
                        "message": "Quiero algo tematico para una nina",
                        "history": [],
                    }
                ),
                content_type='application/json',
                secure=True,
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "fallback")
        self.assertIn("temática", payload["reply"].lower())
        self.assertTrue(payload["actions"])

    def test_asistente_puede_responder_en_modo_ai(self):
        with mock.patch(
            "productos.assistant_views.get_assistant_reply",
            return_value={
                "message": "Te recomiendo revisar tematicos e infantiles y luego confirmar por WhatsApp.",
                "mode": "ai",
                "configured": True,
                "actions": [{"label": "Ver catálogo", "href": "/#catalogo"}],
            },
        ):
            response = self.client.post(
                reverse('assistant_chat'),
                data=json.dumps(
                    {
                        "message": "Tengo 80 mil para un detalle infantil",
                        "history": [{"role": "user", "text": "Hola"}],
                    }
                ),
                content_type='application/json',
                secure=True,
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "ai")
        self.assertTrue(payload["configured"])
        self.assertIn("whatsapp", payload["reply"].lower())

    def test_asistente_valida_mensaje_vacio(self):
        response = self.client.post(
            reverse('assistant_chat'),
            data=json.dumps({"message": "   ", "history": []}),
            content_type='application/json',
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])


class CatalogManagementCommandTests(TestCase):
    def test_import_catalog_products_dry_run_no_escribe_en_db(self):
        temp_path = Path('.tmp-test-media') / 'catalog-import' / 'productos.json'
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            temp_path.write_text(
                json.dumps(
                    [
                        {
                            'nombre': 'Detalle temporal',
                            'categoria': 'Pruebas',
                            'descripcion': 'Producto de prueba.',
                            'precio': '45000.00',
                            'stock': 7,
                            'imagen': 'productos/prueba.jpeg',
                        }
                    ]
                ),
                encoding='utf-8',
            )

            output = StringIO()
            call_command('import_catalog_products', str(temp_path), '--dry-run', stdout=output)

            self.assertIn('DRY RUN', output.getvalue())
            self.assertFalse(Producto.objects.filter(nombre='Detalle temporal').exists())
        finally:
            shutil.rmtree(temp_path.parent.parent, ignore_errors=True)
