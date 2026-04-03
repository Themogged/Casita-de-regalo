import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, ProgrammingError


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Crea un superusuario desde variables de entorno si no existe."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write(
                self.style.WARNING(
                    "Superusuario omitido: faltan DJANGO_SUPERUSER_USERNAME, "
                    "DJANGO_SUPERUSER_EMAIL o DJANGO_SUPERUSER_PASSWORD."
                )
            )
            return

        user_model = get_user_model()
        username_field = user_model.USERNAME_FIELD
        email_field = getattr(user_model, "EMAIL_FIELD", "email")
        lookup = {username_field: username}
        defaults = {
            "is_staff": True,
            "is_superuser": True,
        }

        if email_field:
            defaults[email_field] = email

        try:
            user, created = user_model._default_manager.get_or_create(
                **lookup,
                defaults=defaults,
            )
        except (OperationalError, ProgrammingError) as exc:
            raise CommandError(
                "No se pudo asegurar el superusuario. Ejecuta migrate antes."
            ) from exc

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superusuario '{username}' creado automaticamente."
                )
            )
            return

        changed = False

        if email_field and getattr(user, email_field, None) != email:
            setattr(user, email_field, email)
            changed = True

        if not user.is_staff:
            user.is_staff = True
            changed = True

        if not user.is_superuser:
            user.is_superuser = True
            changed = True

        if env_bool("DJANGO_SUPERUSER_RESET_PASSWORD", False):
            user.set_password(password)
            changed = True

        if changed:
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superusuario '{username}' actualizado automaticamente."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Superusuario '{username}' ya existe. No se hicieron cambios."
            )
        )
