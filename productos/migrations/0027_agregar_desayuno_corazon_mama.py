from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Para mujer"

PRODUCT_NAME = "Desayuno corazón de mamá"


def add_heart_breakfast(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    Producto.objects.update_or_create(
        nombre=PRODUCT_NAME,
        defaults={
            "descripcion": (
                "Desayuno en bandeja de corazón con mini waffles con queso y fruta, "
                "fresas, uchuvas, arándanos, masmelos, galletas de queso, jugo, "
                "frasquito con miel, pin decorativo y tarjeta. Precio base sujeto "
                "a disponibilidad de insumos y personalización."
            ),
            "precio": Decimal("74000.00"),
            "stock": 100,
            "categoria": categoria,
            "imagen": "productos/mujer/desayuno-corazon-de-mama-20260514.jpeg",
            "destacado": False,
        },
    )


def remove_heart_breakfast(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0026_agregar_desayuno_mama_lo_mejor"),
    ]

    operations = [
        migrations.RunPython(add_heart_breakfast, remove_heart_breakfast),
    ]
