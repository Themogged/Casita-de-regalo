import json
import os

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from tienda_regalos.middleware import AdminRateLimitMiddleware, SecurityHeadersMiddleware


class EnsureSuperuserCommandTests(TestCase):
    def setUp(self):
        self.original_env = {
            "DJANGO_SUPERUSER_USERNAME": os.environ.get("DJANGO_SUPERUSER_USERNAME"),
            "DJANGO_SUPERUSER_EMAIL": os.environ.get("DJANGO_SUPERUSER_EMAIL"),
            "DJANGO_SUPERUSER_PASSWORD": os.environ.get("DJANGO_SUPERUSER_PASSWORD"),
            "DJANGO_SUPERUSER_RESET_PASSWORD": os.environ.get("DJANGO_SUPERUSER_RESET_PASSWORD"),
        }

    def tearDown(self):
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_ensure_superuser_crea_usuario_cuando_hay_variables(self):
        os.environ["DJANGO_SUPERUSER_USERNAME"] = "adminrender"
        os.environ["DJANGO_SUPERUSER_EMAIL"] = "adminrender@example.com"
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = "ClaveSegura123!"

        call_command("ensure_superuser")

        user_model = get_user_model()
        user = user_model.objects.get(username="adminrender")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.email, "adminrender@example.com")

    def test_ensure_superuser_no_crea_usuario_si_faltan_variables(self):
        os.environ.pop("DJANGO_SUPERUSER_USERNAME", None)
        os.environ.pop("DJANGO_SUPERUSER_EMAIL", None)
        os.environ.pop("DJANGO_SUPERUSER_PASSWORD", None)

        call_command("ensure_superuser")

        user_model = get_user_model()
        self.assertEqual(user_model.objects.count(), 0)


class SecurityHeadersMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _get_response(self, path="/"):
        middleware = SecurityHeadersMiddleware(lambda request: HttpResponse("ok"))
        return middleware(self.factory.get(path))

    def test_agrega_headers_defensivos(self):
        response = self._get_response("/")

        self.assertIn("Content-Security-Policy", response)
        self.assertIn("https://fonts.googleapis.com", response["Content-Security-Policy"])
        self.assertIn("https://fonts.gstatic.com", response["Content-Security-Policy"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["Origin-Agent-Cluster"], "?1")

    def test_admin_no_debe_quedar_cacheado(self):
        response = self._get_response("/admin/")

        self.assertEqual(response["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertEqual(response["Expires"], "0")

    def test_cuenta_y_carrito_no_deben_quedar_cacheados(self):
        for path in ("/cuenta/", "/cuenta/memoria/", "/carrito/"):
            with self.subTest(path=path):
                response = self._get_response(path)
                self.assertEqual(
                    response["Cache-Control"],
                    "no-store, no-cache, must-revalidate, max-age=0",
                )


class LoginRateLimitMiddlewareTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    @override_settings(
        CUSTOMER_LOGIN_MAX_ATTEMPTS=1,
        CUSTOMER_LOGIN_BLOCK_MINUTES=5,
    )
    def test_bloquea_temporalmente_login_de_cliente_sin_exponer_credenciales(self):
        cache.set("customer-login-attempts:127.0.0.1", 1, timeout=300)
        request = self.factory.post(
            "/cuenta/ingresar/",
            {"username": "cliente", "password": "secreto"},
            REMOTE_ADDR="127.0.0.1",
        )
        middleware = AdminRateLimitMiddleware(lambda request: HttpResponse("ok"))

        response = middleware(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "300")
        self.assertNotContains(response, "cliente", status_code=429)
        self.assertNotContains(response, "secreto", status_code=429)

    @override_settings(
        CUSTOMER_LOGIN_MAX_ATTEMPTS=1,
        CUSTOMER_LOGIN_BLOCK_MINUTES=5,
    )
    def test_bloquea_intentos_repetidos_de_cambio_de_contrasena(self):
        cache.set("customer-login-attempts:127.0.0.1", 1, timeout=300)
        request = self.factory.post(
            "/cuenta/cambiar-clave/",
            {"username": "cliente", "current_password": "secreto"},
            REMOTE_ADDR="127.0.0.1",
        )
        middleware = AdminRateLimitMiddleware(lambda request: HttpResponse("ok"))

        response = middleware(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "300")
        self.assertNotContains(response, "cliente", status_code=429)
        self.assertNotContains(response, "secreto", status_code=429)


class ResponseCompressionTests(TestCase):
    def test_comprime_html_publico_para_clientes_compatibles(self):
        response = self.client.get("/", HTTP_ACCEPT_ENCODING="gzip")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Encoding"], "gzip")
        self.assertIn("Accept-Encoding", response["Vary"])


class TelemetryTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_acepta_evento_y_descarta_contexto_no_autorizado(self):
        with self.assertLogs("storefront.events", level="INFO") as captured:
            response = self.client.post(
                reverse("collect_event"),
                data=json.dumps(
                    {
                        "event": "cart_add",
                        "path": "/catalogo/?correo=privado@example.com",
                        "product_id": 12,
                        "context": {
                            "status": "added",
                            "email": "privado@example.com",
                        },
                    }
                ),
                content_type="application/json",
                secure=True,
            )

        self.assertEqual(response.status_code, 202)
        self.assertIn('\"path\":\"/catalogo/\"', captured.output[0])
        self.assertNotIn("privado@example.com", captured.output[0])

    def test_rechaza_evento_desconocido(self):
        response = self.client.post(
            reverse("collect_event"),
            data=json.dumps({"event": "capturar_datos"}),
            content_type="application/json",
            secure=True,
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(TELEMETRY_EVENTS_PER_MINUTE=1)
    def test_limita_rafagas_de_eventos(self):
        payload = json.dumps({"event": "page_view"})
        first = self.client.post(reverse("collect_event"), payload, content_type="application/json")
        second = self.client.post(reverse("collect_event"), payload, content_type="application/json")

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 429)
