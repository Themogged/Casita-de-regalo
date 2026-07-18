import hashlib
import json

import carrito.models
import django.core.validators
from django.db import migrations, models


def populate_configuration_keys(apps, schema_editor):
    CartItem = apps.get_model("carrito", "CarritoItem")
    for item in CartItem.objects.all().iterator():
        payload = {
            "texto_personalizado": (item.texto_personalizado or "").strip(),
            "color": (item.color or "").strip(),
            "variante": (item.variante or "").strip(),
            "fecha_entrega": item.fecha_entrega.isoformat() if item.fecha_entrega else "",
            "mensaje_regalo": (item.mensaje_regalo or "").strip(),
            "opciones": {},
            "imagen_hash": "",
        }
        if item.imagen_cliente:
            payload["imagen_hash"] = hashlib.sha256(item.imagen_cliente.name.encode("utf-8")).hexdigest()
        canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        item.imagen_hash = payload["imagen_hash"]
        item.configuration_key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        item.save(update_fields=["imagen_hash", "configuration_key"])


class Migration(migrations.Migration):
    dependencies = [("carrito", "0002_carrito_cart_has_exactly_one_owner")]

    operations = [
        migrations.RemoveConstraint(
            model_name="carritoitem",
            name="unique_product_per_persistent_cart",
        ),
        migrations.AddField(
            model_name="carritoitem",
            name="configuration_key",
            field=models.CharField(db_index=True, default="", editable=False, max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="carritoitem",
            name="imagen_hash",
            field=models.CharField(blank=True, editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="carritoitem",
            name="opciones",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="carritoitem",
            name="imagen_cliente",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=carrito.models.customer_image_upload_to,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        ["jpg", "jpeg", "png", "webp"]
                    ),
                    carrito.models.validate_customer_image_size,
                ],
            ),
        ),
        migrations.RunPython(populate_configuration_keys, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="carritoitem",
            constraint=models.UniqueConstraint(
                fields=("carrito", "producto", "configuration_key"),
                name="unique_configured_product_per_cart",
            ),
        ),
    ]
