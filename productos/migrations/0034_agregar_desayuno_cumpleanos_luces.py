from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Cumpleaños y desayunos"
PRODUCT_NAME = "Desayuno cumpleaños con luces"


def add_breakfast_with_lights(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    Producto.objects.update_or_create(
        nombre=PRODUCT_NAME,
        defaults={
            "descripcion": (
                "Desayuno en caja de madera con espaldar, flores, Milo, Bonyurt, "
                "waffles con fresas, cupcake, pocillo, mix de frutas, pin decorativo, "
                "decoración y luces. Precio base sujeto a disponibilidad de insumos "
                "y personalización."
            ),
            "precio": Decimal("140000.00"),
            "stock": 100,
            "categoria": categoria,
            "imagen": "",
            "destacado": False,
        },
    )


def remove_breakfast_with_lights(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0033_agregar_desayunos_generales"),
    ]

    operations = [
        migrations.RunPython(add_breakfast_with_lights, remove_breakfast_with_lights),
    ]
