from datetime import date, timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from carrito.models import Carrito, CarritoItem
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
        self.checkout_data = {
            'para_quien': 'Laura',
            'fecha_entrega': (date.today() + timedelta(days=2)).isoformat(),
        }

    def test_agregar_redirige_al_catalogo_con_anchor_si_viene_del_inicio(self):
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_REFERER='https://testserver/?q=desayuno',
            secure=True,
        )

        self.assertRedirects(
            response,
            '/catalogo/#catalogo',
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

    def test_carrito_no_muestra_stock_publico(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.get(reverse('ver_carrito'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Stock disponible')
        self.assertNotContains(response, '3 unidades')

    def test_carrito_mantiene_contrato_de_checkout(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.get(reverse('ver_carrito'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'js-whatsapp-checkout-form')
        self.assertContains(response, 'js-whatsapp-checkout-button')
        self.assertContains(response, 'Lista para cotizar')
        self.assertContains(response, 'Datos para personalizar')
        self.assertContains(response, 'name="ocasion"')
        self.assertContains(response, 'name="para_quien"')
        self.assertContains(response, 'name="fecha_entrega"')
        self.assertContains(response, 'data-min-today')
        self.assertContains(response, 'name="mensaje_tarjeta"')
        self.assertContains(response, 'name="detalle_extra"')
        self.assertContains(response, 'Cotizar por WhatsApp')
        self.assertContains(response, 'mobile-checkout-panel')
        self.assertContains(response, 'js-cart-update-form')
        self.assertContains(response, 'data-cart-total-label')
        self.assertContains(response, 'data-cart-row')
        self.assertNotContains(response, 'Cotizaci&oacute;n premium')
        self.assertNotContains(response, 'brief')

    def test_carrito_vacio_muestra_lista_para_cotizar(self):
        response = self.client.get(reverse('ver_carrito'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A&uacute;n no has elegido tu sorpresa')
        self.assertContains(response, 'Explorar cat&aacute;logo')
        self.assertNotContains(response, 'Tu carrito est&aacute; vac&iacute;o')

    def test_agregar_por_ajax_responde_sin_redireccion(self):
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['ok'], True)
        self.assertEqual(data['level'], 'success')
        self.assertEqual(data['message'], 'Desayuno prueba agregado a tu lista.')
        self.assertEqual(data['cart_total'], 1)
        self.assertEqual(data['product_id'], self.producto.id)
        self.assertEqual(data['product_name'], self.producto.nombre)
        self.assertEqual(data['item_quantity'], 1)
        self.assertEqual(data['quantity_updated'], False)
        self.assertEqual(data['cart']['units'], 1)
        self.assertEqual(data['cart']['items'][0]['product_id'], self.producto.id)

    def test_agregar_mismo_producto_por_ajax_actualiza_cantidad(self):
        self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Cantidad actualizada.')
        self.assertEqual(data['quantity_updated'], True)
        self.assertEqual(data['item_quantity'], 2)
        self.assertEqual(data['cart_total'], 2)
        self.assertEqual(len(data['cart']['items']), 1)

    def test_catalogo_incluye_animacion_de_agregar_a_lista(self):
        response = self.client.get(reverse('inicio'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'confirmAddToCart')
        self.assertContains(response, 'is-confirmed')
        self.assertContains(response, 'message--toast')
        self.assertContains(response, 'cart-added')
        self.assertContains(response, 'has-action')
        self.assertContains(response, '.message.message--toast')
        self.assertContains(response, 'toast-action')
        self.assertContains(response, 'toast-thumbnail')
        self.assertContains(response, 'toast-dismiss')
        self.assertContains(response, "new CustomEvent('cart:open'")
        self.assertNotContains(response, 'openDrawer: data.ok === true')
        self.assertContains(response, 'getToastMeta')
        self.assertNotContains(response, '#2d9d78')
        self.assertNotContains(response, '#d99114')
        self.assertNotContains(response, '#d65a5a')

    def test_agregar_no_acepta_get(self):
        response = self.client.get(reverse('agregar_carrito', args=[self.producto.id]), secure=True)

        self.assertEqual(response.status_code, 405)

    def test_sumar_producto_por_ajax_actualiza_totales(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.post(
            reverse('sumar_producto', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['ok'], True)
        self.assertEqual(data['cart_total'], 2)
        self.assertEqual(data['references_count'], 1)
        self.assertEqual(data['item_quantity'], 2)
        self.assertEqual(data['total_label'], '$162.000')
        self.assertEqual(data['item_subtotal_label'], '$162.000')
        self.assertEqual(self.client.session['carrito'][str(self.producto.id)], 2)

    def test_restar_producto_por_ajax_informa_carrito_vacio(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.post(
            reverse('restar_producto', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['ok'], True)
        self.assertEqual(data['cart_total'], 0)
        self.assertEqual(data['references_count'], 0)
        self.assertEqual(data['item_quantity'], 0)
        self.assertEqual(data['item_removed'], True)
        self.assertEqual(data['is_empty'], True)
        self.assertEqual(self.client.session.get('carrito'), {})

    def test_carrito_incluye_toasts_para_actualizar_y_retirar(self):
        response = self.client.get(reverse('ver_carrito'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cart-updated')
        self.assertContains(response, 'cart-removed')
        self.assertContains(response, 'Retirado de la lista')
        self.assertContains(response, 'No se pudo actualizar')

    def test_finalizar_compra_redirige_a_whatsapp_y_descuenta_stock(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.post(reverse('comprar_whatsapp'), self.checkout_data, secure=True)

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
        self.assertEqual(pedido.fecha_entrega, date.fromisoformat(self.checkout_data['fecha_entrega']))

    def test_finalizar_compra_por_ajax_responde_con_url_de_whatsapp(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 1}
        session.save()

        response = self.client.post(
            reverse('comprar_whatsapp'),
            self.checkout_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ok'], True)
        self.assertEqual(response.json()['cart_total'], 0)
        self.assertIn('https://wa.me/573116262155?text=', response.json()['whatsapp_url'])

    def test_carrito_persistente_importa_y_refleja_la_sesion(self):
        session = self.client.session
        session['carrito'] = {str(self.producto.id): 2}
        session.save()

        response = self.client.get(reverse('ver_carrito'), secure=True)

        self.assertEqual(response.status_code, 200)
        persistent_id = self.client.session['persistent_cart_id']
        item = CarritoItem.objects.get(carrito_id=persistent_id, producto=self.producto)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(self.client.session['carrito'][str(self.producto.id)], 2)

    def test_carrito_persistente_exige_un_solo_propietario(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrito.objects.create()

    def test_carrito_anonimo_se_fusiona_al_iniciar_sesion(self):
        self.client.post(reverse('agregar_carrito', args=[self.producto.id]), secure=True)
        user = get_user_model().objects.create_user('cliente-prueba', password='ClaveSegura123!')

        self.assertTrue(self.client.login(username=user.username, password='ClaveSegura123!'))
        response = self.client.get(reverse('ver_carrito'), secure=True)

        self.assertEqual(response.status_code, 200)
        cart = Carrito.objects.get(usuario=user)
        self.assertEqual(cart.items.get(producto=self.producto).cantidad, 1)
        self.assertFalse(Carrito.objects.filter(usuario__isnull=True).exists())

    def test_fusion_suma_cantidades_sin_superar_el_stock(self):
        user = get_user_model().objects.create_user(
            "cliente-con-lista",
            password="ClaveSegura123!",
        )
        user_cart = Carrito.objects.create(usuario=user)
        CarritoItem.objects.create(
            carrito=user_cart,
            producto=self.producto,
            cantidad=1,
        )
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), secure=True)

        self.assertTrue(
            self.client.login(username=user.username, password="ClaveSegura123!")
        )

        user_cart.refresh_from_db()
        self.assertEqual(user_cart.items.get(producto=self.producto).cantidad, 2)

    def test_agregar_guarda_personalizacion_y_la_expone_en_resumen(self):
        delivery_date = (date.today() + timedelta(days=3)).isoformat()
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            {
                'texto_personalizado': 'Feliz cumple, Laura',
                'color': 'Rosa suave',
                'variante': 'Mediano',
                'fecha_entrega': delivery_date,
                'mensaje_regalo': 'Que tengas un dia hermoso',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        item = CarritoItem.objects.get(producto=self.producto)
        self.assertEqual(item.texto_personalizado, 'Feliz cumple, Laura')
        self.assertEqual(item.fecha_entrega.isoformat(), delivery_date)
        self.assertIn('Rosa suave', response.json()['cart']['items'][0]['personalization'])

    def test_agregar_imagen_valida_la_expone_como_vista_previa(self):
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), "#f4a3c3").save(image_buffer, format="PNG")
        upload = SimpleUploadedFile(
            "referencia.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )

        storages = {
            "default": {
                "BACKEND": "django.core.files.storage.InMemoryStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
        with self.settings(STORAGES=storages):
            response = self.client.post(
                reverse("agregar_carrito", args=[self.producto.id]),
                {"imagen_cliente": upload},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                secure=True,
            )

            self.assertEqual(response.status_code, 200)
            item = CarritoItem.objects.get(producto=self.producto)
            self.assertTrue(item.imagen_cliente.name.endswith(".png"))
            preview_url = response.json()["cart"]["items"][0]["personalization_data"][
                "customer_image_url"
            ]
            self.assertIn("/media/personalizaciones/", preview_url)

    def test_agregar_rechaza_fecha_de_personalizacion_pasada_sin_mutar_carrito(self):
        response = self.client.post(
            reverse('agregar_carrito', args=[self.producto.id]),
            {'fecha_entrega': (date.today() - timedelta(days=1)).isoformat()},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['ok'], False)
        self.assertEqual(CarritoItem.objects.count(), 0)

    def test_mismo_producto_con_personalizacion_distinta_crea_lineas_separadas(self):
        first = self.client.post(
            reverse("agregar_carrito", args=[self.producto.id]),
            {"color": "Rosa"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )
        second = self.client.post(
            reverse("agregar_carrito", args=[self.producto.id]),
            {"color": "Lila"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(CarritoItem.objects.filter(producto=self.producto).count(), 2)
        self.assertEqual(second.json()["cart"]["references"], 2)
        self.assertEqual(second.json()["cart"]["units"], 2)
        self.assertEqual(self.client.session["carrito"][str(self.producto.id)], 2)

    def test_personalizacion_identica_incrementa_la_misma_linea(self):
        payload = {"texto_personalizado": "Para Laura", "color": "Rosa"}
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), payload, secure=True)
        response = self.client.post(
            reverse("agregar_carrito", args=[self.producto.id]),
            payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )

        item = CarritoItem.objects.get(producto=self.producto)
        self.assertEqual(item.cantidad, 2)
        self.assertTrue(response.json()["quantity_updated"])
        self.assertEqual(response.json()["item_id"], item.id)

    def test_cantidad_se_actualiza_por_linea_sin_tocar_otra_personalizacion(self):
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Rosa"}, secure=True)
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Lila"}, secure=True)
        pink = CarritoItem.objects.get(color="Rosa")
        lilac = CarritoItem.objects.get(color="Lila")

        response = self.client.post(
            reverse("sumar_item", args=[pink.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )

        pink.refresh_from_db()
        lilac.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item_id"], pink.id)
        self.assertEqual(pink.cantidad, 2)
        self.assertEqual(lilac.cantidad, 1)

    def test_ruta_heredada_no_falla_si_existen_variantes_del_mismo_producto(self):
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Rosa"}, secure=True)
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Lila"}, secure=True)
        first_item = CarritoItem.objects.filter(producto=self.producto).order_by("id").first()

        response = self.client.post(
            reverse("sumar_producto", args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            secure=True,
        )

        first_item.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(first_item.cantidad, 2)
        self.assertEqual(CarritoItem.objects.filter(producto=self.producto).count(), 2)

    def test_editar_personalizacion_independiente_actualiza_su_clave(self):
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Rosa"}, secure=True)
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Lila"}, secure=True)
        item = CarritoItem.objects.get(color="Rosa")
        original_key = item.configuration_key

        response = self.client.post(
            reverse("editar_item_personalizacion", args=[item.id]),
            {"color": "Coral", "texto_personalizado": "Para mamá"},
            secure=True,
        )

        item.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(item.color, "Coral")
        self.assertEqual(item.texto_personalizado, "Para mamá")
        self.assertNotEqual(item.configuration_key, original_key)
        self.assertTrue(CarritoItem.objects.filter(color="Lila").exists())

    def test_checkout_conserva_cada_configuracion_como_linea(self):
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Rosa"}, secure=True)
        self.client.post(reverse("agregar_carrito", args=[self.producto.id]), {"color": "Lila"}, secure=True)

        response = self.client.post(reverse("comprar_whatsapp"), self.checkout_data, secure=True)

        self.assertEqual(response.status_code, 302)
        order = Pedido.objects.get()
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(
            {item.personalizacion["color"] for item in order.items.all()},
            {"Rosa", "Lila"},
        )

    def test_checkout_exige_destinatario_y_fecha(self):
        self.client.post(reverse('agregar_carrito', args=[self.producto.id]), secure=True)

        response = self.client.post(
            reverse('comprar_whatsapp'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['ok'], False)
        self.assertEqual(Pedido.objects.count(), 0)
