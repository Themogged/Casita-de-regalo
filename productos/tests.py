from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Producto, ProductoImagen


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
        self.assertContains(response, 'Formas de confirmar tu pedido')
        self.assertContains(response, 'Explora por categoría')

    def test_inicio_envia_headers_de_seguridad(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertIn('Permissions-Policy', response.headers)

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
