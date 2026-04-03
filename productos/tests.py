from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Producto


class CatalogoViewsTests(TestCase):
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
        self.assertContains(response, 'Categorías favoritas')

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

    def test_catalogo_marca_productos_agotados(self):
        response = self.client.get(reverse('inicio'), {'q': 'ramo'}, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ramo premium')
        self.assertContains(response, 'Agotado')

    def test_catalogo_mantiene_anchor_en_paginacion_y_filtros(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/#catalogo"')
        self.assertContains(response, '?q=&categoria=&orden=destacados&page=2#catalogo')
        self.assertContains(
            response,
            f'{reverse("inicio")}?categoria={self.categoria_regalos.id}#catalogo',
        )
