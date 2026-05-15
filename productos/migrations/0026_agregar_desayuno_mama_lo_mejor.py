from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Para mujer"

PRODUCT_NAME = "Desayuno mamá lo mejor del mundo"


def add_mom_breakfast(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    Producto.objects.update_or_create(
        nombre=PRODUCT_NAME,
        defaults={
            "descripcion": (
                "Desayuno en caja de cartón con yogurt, pastel de pollo, mix de fruta, "
                "café con leche, almojábana, decoración y tarjeta. Precio base sujeto "
                "a disponibilidad de insumos y personalización."
            ),
            "precio": Decimal("67000.00"),
            "stock": 100,
            "categoria": categoria,
            "imagen": "productos/mujer/desayuno-mama-lo-mejor-del-mundo-20260514.jpeg",
            "destacado": False,
        },
    )


def remove_mom_breakfast(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0025_agregar_desayunos_mama_premium"),
    ]

    operations = [
        migrations.RunPython(add_mom_breakfast, remove_mom_breakfast),
    ]
