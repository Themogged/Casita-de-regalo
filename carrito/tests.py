from django.test import TestCase
from django.urls import reverse

from pedidos.models import Pedido
from productos.models import Categoria, Producto


class CarritoViewsTests(TestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nombre='Cumpleaños test')
        self.producto = Producto.objects.create(
            nombre='Desayuno prueba',
            descripcion='Detalle para validar carrito.',
            precio='81000.00',
            stock=3,
            categoria=categoria,
        )

    def test_agregar_redirige_al_catalogo_con_anchor_si_viene_del_inicio(self):
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_REFERER='https://testserver/?q=desayuno',
            secure=True,
        )

        self.assertRedirects(
            response,
            'https://testserver/?q=desayuno#catalogo',
            fetch_redirect_response=False,
        )

    def test_agregar_redirige_a_la_ficha_si_viene_desde_detalle(self):
        detalle = f"https://testserver{reverse('detalle_producto', args=[self.producto.id])}"
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_REFERER=detalle,
            secure=True,
        )

        self.assertRedirects(response, detalle, fetch_redirect_response=False)

    def test_carrito_muestra_precios_formateados_en_cop(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.get(reverse('ver_carrito'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '$81.000')

    def test_agregar_por_ajax_responde_sin_redireccion(self):
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'ok': True,
                'level': 'success',
                'message': 'Desayuno prueba agregado al carrito.',
                'cart_total': 1,
                'product_id': self.producto.id,
            },
        )

    def test_agregar_no_acepta_get(self):
        response = self.client.get(reverse('agregar_carrito', args=[self.producto.id]), secure=True)

        self.assertEqual(response.status_code, 405)

    def test_finalizar_compra_redirige_a_whatsapp_y_descuenta_stock(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.post(reverse('comprar_whatsapp'), secure=True)

        pedido = Pedido.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response['Location'].startswith('https://wa.me/573116262155?text=')
        )
        self.assertIn(f'Pedido%20%23{pedido.id}', response['Location'])
        self.assertIn('Desayuno%20prueba%20x1', response['Location'])

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 2)
        self.assertEqual(self.client.session.get('carrito', {}), {})

    def test_finalizar_compra_por_ajax_responde_con_url_de_whatsapp(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.post(
            reverse('comprar_whatsapp'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ok'], True)
        self.assertEqual(response.json()['cart_total'], 0)
        self.assertIn('https://wa.me/573116262155?text=', response.json()['whatsapp_url'])
