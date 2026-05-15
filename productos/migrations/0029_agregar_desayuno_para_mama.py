from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Para mujer"
PRODUCT_NAME = "Desayuno para mamá"


def add_breakfast_for_mom(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    Producto.objects.update_or_create(
        nombre=PRODUCT_NAME,
        defaults={
            "descripcion": (
                "Desayuno en caja de madera con espaldar pintado, arco de globos, "
                "globo burbuja, jugo, waffles con queso y fruta, mix de fruta, maní "
                "La Especial, chocolatina Jumbo mediana, mini cake y decoración. "
                "Precio base sujeto a disponibilidad de insumos y personalización."
            ),
            "precio": Decimal("130000.00"),
            "stock": 100,
            "categoria": categoria,
            "imagen": "productos/mujer/desayuno-para-mama-20260514.jpeg",
            "destacado": False,
        },
    )


def remove_breakfast_for_mom(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0028_corregir_desayuno_te_quiero_mami"),
    ]

    operations = [
        migrations.RunPython(add_breakfast_for_mom, remove_breakfast_for_mom),
    ]
