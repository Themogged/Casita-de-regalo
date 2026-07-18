import hashlib
import json
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image, UnidentifiedImageError

from productos.models import Producto


ALLOWED_CUSTOMER_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def customer_image_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    return f"personalizaciones/{uuid4().hex}{suffix}"


def validate_customer_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("La imagen no debe superar 5 MB.")
    position = image.tell() if hasattr(image, "tell") else 0
    try:
        with Image.open(image) as opened:
            opened.verify()
            if opened.format not in ALLOWED_CUSTOMER_IMAGE_FORMATS:
                raise ValidationError("Usa una imagen JPG, PNG o WebP.")
            if opened.width * opened.height > 20_000_000:
                raise ValidationError("La imagen tiene dimensiones demasiado grandes.")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError("El archivo seleccionado no es una imagen válida.") from exc
    finally:
        if hasattr(image, "seek"):
            image.seek(position)


class Carrito(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carrito_persistente",
        blank=True,
        null=True,
    )
    session_key = models.CharField(max_length=40, unique=True, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def clean(self):
        if bool(self.usuario_id) == bool(self.session_key):
            raise ValidationError("El carrito debe pertenecer a un usuario o a una sesión.")

    def __str__(self):
        owner = self.usuario.get_username() if self.usuario_id else self.session_key
        return f"Lista de {owner}"

    class Meta:
        ordering = ["-actualizado"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(usuario__isnull=False, session_key__isnull=True)
                    | models.Q(usuario__isnull=True, session_key__isnull=False)
                ),
                name="cart_has_exactly_one_owner",
            ),
        ]
        verbose_name = "lista persistente"
        verbose_name_plural = "listas persistentes"


class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="carrito_items")
    cantidad = models.PositiveIntegerField(default=1)
    texto_personalizado = models.CharField(max_length=180, blank=True)
    color = models.CharField(max_length=80, blank=True)
    variante = models.CharField(max_length=80, blank=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    mensaje_regalo = models.TextField(max_length=500, blank=True)
    opciones = models.JSONField(default=dict, blank=True)
    configuration_key = models.CharField(max_length=64, editable=False, db_index=True)
    imagen_hash = models.CharField(max_length=64, blank=True, editable=False)
    imagen_cliente = models.ImageField(
        upload_to=customer_image_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_customer_image_size,
        ],
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    @property
    def personalization_summary(self):
        values = [
            self.texto_personalizado,
            self.color,
            self.variante,
            self.fecha_entrega.isoformat() if self.fecha_entrega else "",
            self.mensaje_regalo,
            "Imagen adjunta" if self.imagen_cliente else "",
        ]
        values.extend(str(value) for value in self.opciones.values() if value)
        return [value for value in values if value]

    def configuration_payload(self):
        return {
            "texto_personalizado": self.texto_personalizado.strip(),
            "color": self.color.strip(),
            "variante": self.variante.strip(),
            "fecha_entrega": self.fecha_entrega.isoformat() if self.fecha_entrega else "",
            "mensaje_regalo": self.mensaje_regalo.strip(),
            "opciones": self.opciones or {},
            "imagen_hash": self.imagen_hash,
        }

    def refresh_configuration_key(self):
        canonical = json.dumps(
            self.configuration_payload(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.configuration_key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self.configuration_key

    def save(self, *args, **kwargs):
        if not self.configuration_key:
            self.refresh_configuration_key()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    class Meta:
        ordering = ["creado", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["carrito", "producto", "configuration_key"],
                name="unique_configured_product_per_cart",
            ),
        ]
        indexes = [models.Index(fields=["carrito", "producto"])]
        verbose_name = "producto de la lista"
        verbose_name_plural = "productos de la lista"
