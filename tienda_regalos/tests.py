import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


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
