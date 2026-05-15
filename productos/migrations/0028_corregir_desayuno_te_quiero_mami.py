from decimal import Decimal

from django.db import migrations


OLD_NAME = "Desayuno para mamá premium"
NEW_NAME = "Desayuno te quiero mami"
NEW_IMAGE = "productos/mujer/desayuno-te-quiero-mami-20260514.jpeg"
OLD_IMAGE = "productos/mujer/desayuno-para-mama-premium-20260514.jpeg"


def update_breakfast(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    producto = (
        Producto.objects.filter(nombre=OLD_NAME).first()
        or Producto.objects.filter(imagen=OLD_IMAGE).first()
        or Producto.objects.filter(nombre=NEW_NAME).first()
    )
    if producto is None:
        return

    producto.nombre = NEW_NAME
    producto.descripcion = (
        "Desayuno en caja de cartón con café capuchino, burrito de carnes y verduras, "
        "jugo, mix de fruta y globo. Precio base sujeto a disponibilidad de insumos "
        "y personalización."
    )
    producto.precio = Decimal("76000.00")
    producto.stock = 100
    producto.imagen = NEW_IMAGE
    producto.destacado = False
    producto.save(
        update_fields=[
            "nombre",
            "descripcion",
            "precio",
            "stock",
            "imagen",
            "destacado",
        ]
    )


def revert_breakfast(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    producto = Producto.objects.filter(nombre=NEW_NAME).first()
    if producto is None:
        return

    producto.nombre = OLD_NAME
    producto.descripcion = (
        "Desayuno en caja de madera con espaldar pintado, arco de globos, "
        "globo burbuja, jugo, waffles con queso y fruta, mix de fruta, maní "
        "La Especial, chocolatina Jumbo mediana, mini cake y decoración. "
        "Precio base sujeto a disponibilidad de insumos y personalización."
    )
    producto.precio = Decimal("130000.00")
    producto.imagen = OLD_IMAGE
    producto.save(update_fields=["nombre", "descripcion", "precio", "imagen"])


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0027_agregar_desayuno_corazon_mama"),
    ]

    operations = [
        migrations.RunPython(update_breakfast, revert_breakfast),
    ]
