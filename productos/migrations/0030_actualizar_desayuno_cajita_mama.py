from decimal import Decimal

from django.db import migrations


PRODUCT_NAME = "Desayuno cajita especial para mamá"


def update_special_box_breakfast(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    Producto.objects.filter(nombre=PRODUCT_NAME).update(
        descripcion=(
            "Desayuno en cajita especial para mamá con mini maridaje de quesos, "
            "salami y peperoni, uvas, fresas, mini sándwiches, empanadas de queso, "
            "galletas de chocolate, galletas de queso, salsas, pin decorativo, moño "
            "y arco de globos. Precio base sujeto a disponibilidad de insumos y "
            "personalización."
        ),
        precio=Decimal("100000.00"),
        stock=100,
        imagen="productos/mujer/desayuno-cajita-especial-mama-arco-20260514.jpeg",
        destacado=False,
    )


def revert_special_box_breakfast(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    Producto.objects.filter(nombre=PRODUCT_NAME).update(
        descripcion=(
            "Desayuno en cajita especial para mamá con mini maridaje de quesos, "
            "salami y peperoni, uvas, fresas, mini sándwiches, empanadas de queso, "
            "galletas de chocolate, galletas de queso, salsas, pin decorativo y moño. "
            "Precio base sujeto a disponibilidad de insumos y personalización."
        ),
        precio=Decimal("85000.00"),
        imagen="productos/mujer/desayuno-cajita-especial-mama-20260514.jpeg",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0029_agregar_desayuno_para_mama"),
    ]

    operations = [
        migrations.RunPython(update_special_box_breakfast, revert_special_box_breakfast),
    ]
