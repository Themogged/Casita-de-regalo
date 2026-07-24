from datetime import date

from django.conf import settings
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

    def test_login_usa_identidad_oficial_y_controles_accesibles(self):
        response = self.client.get(reverse("login"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "branding/logo-casita.jpeg")
        self.assertNotContains(response, "logo-casita-720w.webp")
        self.assertContains(response, 'class="login-mobile-mark"')
        self.assertContains(
            response,
            "Logo oficial de Casita de Regalos, una casa rosada con un coraz&oacute;n",
        )
        self.assertContains(response, 'autocomplete="username"')
        self.assertContains(response, 'autocomplete="current-password"')
        self.assertContains(response, 'data-password-toggle')
        self.assertContains(response, 'name="remember_me"')
        self.assertContains(response, 'data-login-submit')
        self.assertContains(response, 'aria-live="polite"')
        self.assertContains(response, 'class="profile-brand-icon"')
        self.assertContains(response, 'class="profile-brand-heart"')

    def test_login_invalido_conserva_usuario_sin_revelar_la_contrasena(self):
        get_user_model().objects.create_user(
            "cliente-login",
            password="ClaveCorrecta2026!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "cliente-login",
                "password": "ClaveIncorrecta2026!",
            },
            secure=True,
            REMOTE_ADDR="10.0.0.21",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pudimos iniciar sesi")
        self.assertContains(response, 'value="cliente-login"')
        self.assertNotContains(response, "ClaveIncorrecta2026!")

    def test_login_recordarme_extiende_la_sesion(self):
        get_user_model().objects.create_user(
            "cliente-recordado",
            password="ClaveSegura2026!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "cliente-recordado",
                "password": "ClaveSegura2026!",
                "remember_me": "on",
            },
            secure=True,
            REMOTE_ADDR="10.0.0.22",
        )

        self.assertRedirects(response, reverse("account_profile"))
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertGreaterEqual(
            self.client.session.get_expiry_age(),
            settings.SESSION_COOKIE_AGE - 10,
        )

    def test_login_sin_recordarme_expira_al_cerrar_el_navegador(self):
        get_user_model().objects.create_user(
            "cliente-temporal",
            password="ClaveSegura2026!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "cliente-temporal",
                "password": "ClaveSegura2026!",
            },
            secure=True,
            REMOTE_ADDR="10.0.0.23",
        )

        self.assertRedirects(response, reverse("account_profile"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

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
        self.assertContains(response, "account-profile-page")
        self.assertContains(response, 'class="account-profile-mark"')
        self.assertContains(response, 'class="profile-brand-body"')
        self.assertContains(response, 'class="profile-brand-heart"')
        self.assertNotContains(response, "brand-casita-circle.svg")

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

    def test_cambio_de_contrasena_abre_directamente_sin_sesion(self):
        response = self.client.get(reverse("password_change"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Actualiza tu contrase")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, "Usuario y contrase")

    def test_pantalla_de_cambio_explica_el_flujo_sin_correo(self):
        user = get_user_model().objects.create_user("cliente-clave", password="ClaveActual2026!")
        self.client.force_login(user)

        response = self.client.get(reverse("password_change"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Actualiza tu contrase")
        self.assertContains(response, "No necesitas correo")
        self.assertContains(response, "brand-casita-isotype.svg")
        self.assertNotContains(response, 'name="username" type="text"')

    def test_cambio_rechaza_una_contrasena_actual_incorrecta(self):
        user = get_user_model().objects.create_user("cliente-error", password="ClaveActual2026!")
        self.client.force_login(user)

        response = self.client.post(
            reverse("password_change"),
            {
                "current_password": "ClaveIncorrecta2026!",
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
                "current_password": "ClaveActual2026!",
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

    def test_cambio_sin_sesion_valida_la_clave_actual_e_inicia_sesion(self):
        user = get_user_model().objects.create_user("cliente-directo", password="ClaveActual2026!")

        response = self.client.post(
            reverse("password_change"),
            {
                "username": "cliente-directo",
                "current_password": "ClaveActual2026!",
                "new_password1": "NuevaClave2026!Segura",
                "new_password2": "NuevaClave2026!Segura",
            },
            secure=True,
        )

        self.assertRedirects(response, reverse("account_profile"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("NuevaClave2026!Segura"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_cambio_sin_sesion_no_revela_si_el_usuario_existe(self):
        response = self.client.post(
            reverse("password_change"),
            {
                "username": "usuario-inexistente",
                "current_password": "ClaveIncorrecta2026!",
                "new_password1": "NuevaClave2026!Segura",
                "new_password2": "NuevaClave2026!Segura",
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pudimos validar el usuario y la contrase")
        self.assertNotContains(response, "usuario inexistente")
