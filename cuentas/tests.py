from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from asistente.models import AssistantProfile
from carrito.models import Carrito
from pedidos.models import Pedido
from productos.models import Categoria, Producto


class AccountViewsTests(TestCase):
    def setUp(self):
        category = Categoria.objects.create(nombre="Cuenta test")
        self.product = Producto.objects.create(
            nombre="Detalle cuenta",
            descripcion="Referencia para probar cuenta",
            precio="90000.00",
            stock=5,
            categoria=category,
        )

    def test_registro_inicia_sesion_y_conserva_lista_anonima(self):
        self.client.post(reverse("agregar_carrito", args=[self.product.pk]), secure=True)

        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "nueva-cliente",
                "first_name": "Laura",
                "email": "laura@example.com",
                "password1": "ClaveDePrueba2026!",
                "password2": "ClaveDePrueba2026!",
            },
            secure=True,
        )

        self.assertRedirects(response, reverse("account_profile"))
        user = get_user_model().objects.get(username="nueva-cliente")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertEqual(Carrito.objects.get(usuario=user).items.get().producto, self.product)
        self.assertTrue(AssistantProfile.objects.filter(user=user, memory_enabled=False).exists())

    def test_perfil_muestra_lista_pedidos_y_acceso_a_memoria(self):
        user = get_user_model().objects.create_user("cliente", password="ClaveSegura123!")
        Pedido.objects.create(usuario=user, total="90000.00", fecha_entrega=date.today())
        self.client.force_login(user)

        response = self.client.get(reverse("account_profile"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mi cuenta")
        self.assertContains(response, "Pedidos recientes")
        self.assertContains(response, "Memoria de Cora")

    def test_perfil_y_memoria_requieren_autenticacion(self):
        profile = self.client.get(reverse("account_profile"), secure=True)
        memory = self.client.get(reverse("assistant_memory"), secure=True)

        self.assertEqual(profile.status_code, 302)
        self.assertIn(reverse("login"), profile["Location"])
        self.assertEqual(memory.status_code, 302)
        self.assertIn(reverse("login"), memory["Location"])

    def test_actualizacion_de_perfil_valida_email_unico(self):
        get_user_model().objects.create_user("ocupado", email="ocupado@example.com")
        user = get_user_model().objects.create_user("cliente", email="libre@example.com")
        self.client.force_login(user)

        response = self.client.post(
            reverse("account_update"),
            {
                "first_name": "Laura",
                "last_name": "Gomez",
                "email": "ocupado@example.com",
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.email, "libre@example.com")

    def test_registro_rechaza_honeypot_sin_crear_usuario(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "robot",
                "first_name": "Robot",
                "email": "robot@example.com",
                "password1": "ClaveDePrueba2026!",
                "password2": "ClaveDePrueba2026!",
                "company": "spam",
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username="robot").exists())

    def test_cambio_de_contrasena_requiere_sesion(self):
        response = self.client.get(reverse("password_change"), secure=True)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.assertIn("next=", response["Location"])

        login_response = self.client.get(response["Location"], secure=True)
        self.assertContains(login_response, "Cambio seguro")
        self.assertContains(login_response, "enseguida podr")

    def test_pantalla_de_cambio_explica_el_flujo_sin_correo(self):
        user = get_user_model().objects.create_user("cliente-clave", password="ClaveActual2026!")
        self.client.force_login(user)

        response = self.client.get(reverse("password_change"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Actualiza tu contrase")
        self.assertContains(response, "sin correos ni enlaces externos")
        self.assertContains(response, "brand-casita-isotype.svg")

    def test_cambio_rechaza_una_contrasena_actual_incorrecta(self):
        user = get_user_model().objects.create_user("cliente-error", password="ClaveActual2026!")
        self.client.force_login(user)

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "ClaveIncorrecta2026!",
                "new_password1": "NuevaClave2026!Segura",
                "new_password2": "NuevaClave2026!Segura",
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("ClaveActual2026!"))

    def test_cambio_actualiza_la_clave_y_conserva_la_sesion(self):
        user = get_user_model().objects.create_user("cliente-seguro", password="ClaveActual2026!")
        self.client.force_login(user)

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "ClaveActual2026!",
                "new_password1": "NuevaClave2026!Segura",
                "new_password2": "NuevaClave2026!Segura",
            },
            secure=True,
        )

        self.assertRedirects(response, reverse("account_profile"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("NuevaClave2026!Segura"))
        self.assertEqual(
            self.client.get(reverse("account_profile"), secure=True).status_code,
            200,
        )
