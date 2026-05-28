from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Cumpleaños y desayunos"
PRODUCT_NAME = "Desayuno tocador"


def add_dresser_breakfast(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    Producto.objects.update_or_create(
        nombre=PRODUCT_NAME,
        defaults={
            "descripcion": (
                "Desayuno en tocador de madera con jugo, mix de fruta, waffles con "
                "queso y fruta, ramo de flores y decoración. Precio base sujeto a "
                "disponibilidad de insumos y personalización."
            ),
            "precio": Decimal("168000.00"),
            "stock": 100,
            "categoria": categoria,
            "imagen": "",
            "destacado": False,
        },
    )


def remove_dresser_breakfast(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0035_agregar_imagen_desayuno_cumpleanos_luces"),
    ]

    operations = [
        migrations.RunPython(add_dresser_breakfast, remove_dresser_breakfast),
    ]
