from django.test import TestCase
from django.urls import reverse

from pedidos.models import Pedido, PedidoItem
from productos.models import Categoria, Producto


class CarritoViewsTests(TestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nombre='Cumpleanos test')
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
            HTTP_REFERER='http://testserver/?q=desayuno',
        )

        self.assertRedirects(response, 'http://testserver/?q=desayuno#catalogo', fetch_redirect_response=False)

    def test_agregar_redirige_a_la_ficha_si_viene_desde_detalle(self):
        detalle = f"http://testserver{reverse('detalle_producto', args=[self.producto.id])}"
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_REFERER=detalle,
        )

        self.assertRedirects(response, detalle, fetch_redirect_response=False)

    def test_carrito_muestra_precios_formateados_en_cop(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.get(reverse('ver_carrito'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '$81.000')

    def test_agregar_por_ajax_responde_sin_redireccion(self):
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
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
        response = self.client.get(reverse('agregar_carrito', args=[self.producto.id]))

        self.assertEqual(response.status_code, 405)

    def test_finalizar_compra_redirige_a_confirmacion_y_descuenta_stock(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.post(reverse('comprar_whatsapp'))

        pedido = Pedido.objects.get()
        self.assertRedirects(
            response,
            reverse('pedido_confirmado', args=[pedido.id]),
        )

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 2)
        self.assertEqual(self.client.session.get('carrito', {}), {})

    def test_confirmacion_muestra_resumen_y_boton_de_whatsapp(self):
        pedido = Pedido.objects.create(total='81000.00')
        PedidoItem.objects.create(
            pedido=pedido,
            producto_nombre='Desayuno prueba',
            cantidad=1,
            precio='81000.00',
        )

        response = self.client.get(reverse('pedido_confirmado', args=[pedido.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'#{pedido.id}')
        self.assertContains(response, 'Abrir WhatsApp')
        self.assertContains(response, '573116262155')
