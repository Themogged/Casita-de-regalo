import json
import os
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image
from unittest import mock

from .image_frames import generate_yellow_child_frame, slugify_filename
from .models import Categoria, InteraccionCliente, Producto, ProductoImagen, VideoElaboracion
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
        self.assertContains(response, 'hero-product-card')
        self.assertContains(response, 'data-track-click="instagram"')

    @override_settings(BUSINESS_WHATSAPP_NUMBER='570000000000')
    def test_inicio_usa_numero_whatsapp_configurado(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://wa.me/570000000000')

    def test_inicio_muestra_videos_de_elaboracion_activos(self):
        VideoElaboracion.objects.create(
            titulo='Armado de detalle personalizado',
            descripcion='Proceso real de decoracion y empaque.',
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
        self.assertContains(sitemap, reverse('como_comprar'))
        self.assertContains(sitemap, reverse('preguntas_frecuentes'))
        self.assertContains(sitemap, reverse('detalle_producto', args=[self.producto_principal.id]))

    def test_registra_interaccion_de_cliente(self):
        response = self.client.post(
            reverse('registrar_interaccion'),
            data=json.dumps(
                {
                    'tipo': 'whatsapp',
                    'etiqueta': 'hero_whatsapp',
                    'destino': 'https://wa.me/573116262155',
                    'pagina': '/',
                }
            ),
            content_type='application/json',
            secure=True,
            HTTP_USER_AGENT='CatalogoTest/1.0',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        evento = InteraccionCliente.objects.get()
        self.assertEqual(evento.tipo, 'whatsapp')
        self.assertEqual(evento.etiqueta, 'hero_whatsapp')
        self.assertEqual(evento.pagina, '/')

    def test_catalogo_filtra_por_categoria(self):
        response = self.client.get(reverse('inicio'), {'categoria': self.categoria_flores.id}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ramo premium')
        self.assertNotContains(response, 'Caja sorpresa')

    def test_detalle_producto_muestra_relacionados(self):
        response = self.client.get(reverse('detalle_producto', args=[self.producto_principal.id]), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Caja sorpresa')
        self.assertContains(response, 'Kit cumpleañero')
        self.assertContains(response, 'Siguiente')
        self.assertContains(response, reverse('detalle_producto', args=[self.relacionado.id]))

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
        self.assertContains(response, '?q=&categoria=&orden=destacados&page=2#catalogo')
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
                "actions": [{"label": "Ver catalogo", "href": "/#catalogo"}],
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
