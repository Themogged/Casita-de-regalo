from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image, UnidentifiedImageError

from productos.models import Producto


def validate_customer_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("La imagen no debe superar 5 MB.")
    position = image.tell() if hasattr(image, "tell") else 0
    try:
        with Image.open(image) as opened:
            opened.verify()
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
    imagen_cliente = models.ImageField(
        upload_to="personalizaciones/%Y/%m/",
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
        return [value for value in values if value]

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    class Meta:
        ordering = ["creado", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["carrito", "producto"],
                name="unique_product_per_persistent_cart",
            ),
        ]
        indexes = [models.Index(fields=["carrito", "producto"])]
        verbose_name = "producto de la lista"
        verbose_name_plural = "productos de la lista"
