from datetime import date
from smtplib import SMTPException
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
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

    def test_flujo_de_recuperacion_tiene_todas_las_pantallas(self):
        response = self.client.get(reverse("password_reset"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recuperar acceso")
        self.assertContains(response, "brand-casita-isotype.svg")
        self.assertEqual(
            self.client.get(reverse("password_reset_done"), secure=True).status_code,
            200,
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Casita de Regalos <hola@example.com>",
    )
    def test_recuperacion_envia_un_enlace_real_al_backend_configurado(self):
        get_user_model().objects.create_user(
            "cliente-correo",
            email="cliente@example.com",
            password="ClaveSegura123!",
        )

        response = self.client.post(
            reverse("password_reset"),
            {"email": "cliente@example.com"},
            secure=True,
        )

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["cliente@example.com"])
        self.assertIn("/cuenta/recuperar/", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="smtp.example.com",
        EMAIL_HOST_USER="sender@example.com",
        EMAIL_HOST_PASSWORD="app-password",
    )
    @mock.patch("cuentas.views.logger.exception")
    @mock.patch(
        "django.contrib.auth.forms.PasswordResetForm.save",
        side_effect=SMTPException("delivery failed"),
    )
    def test_recuperacion_muestra_error_amigable_si_smtp_falla(
        self,
        mocked_save,
        mocked_logger,
    ):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "cliente@example.com"},
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pudimos enviar el enlace")
        mocked_save.assert_called_once()
        mocked_logger.assert_called_once_with("password_reset_email_delivery_failed")
