from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Cumpleaños y desayunos"

PRODUCTS = [
    {
        "nombre": "Desayuno",
        "precio": "70000.00",
        "descripcion": (
            "Mesa de desayuno en madera con arco de globos y flores, mix de frutas, "
            "manzana, pera, té Hatsu y decoración. Precio base sujeto a disponibilidad "
            "de insumos y personalización."
        ),
    },
    {
        "nombre": "Desayuno cajita feliz",
        "precio": "63000.00",
        "descripcion": (
            "Caja en cartón con creps de pollo y verduras, mix de fruta, jugo, globo, "
            "pin decorativo y decoración. Precio base sujeto a disponibilidad de "
            "insumos y personalización."
        ),
    },
]


def add_breakfast_products(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    for item in PRODUCTS:
        Producto.objects.update_or_create(
            nombre=item["nombre"],
            defaults={
                "descripcion": item["descripcion"],
                "precio": Decimal(item["precio"]),
                "stock": 100,
                "categoria": categoria,
                "imagen": "",
                "destacado": False,
            },
        )


def remove_breakfast_products(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre__in=[item["nombre"] for item in PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0032_eliminar_interacciones_cliente"),
    ]

    operations = [
        migrations.RunPython(add_breakfast_products, remove_breakfast_products),
    ]
