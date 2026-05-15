from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Para mujer"

PRODUCTS = [
    {
        "nombre": "Desayuno cajita especial para mamá",
        "precio": "85000.00",
        "imagen": "productos/mujer/desayuno-cajita-especial-mama-20260514.jpeg",
        "descripcion": (
            "Desayuno en cajita especial para mamá con mini maridaje de quesos, "
            "salami y peperoni, uvas, fresas, mini sándwiches, empanadas de queso, "
            "galletas de chocolate, galletas de queso, salsas, pin decorativo y moño. "
            "Precio base sujeto a disponibilidad de insumos y personalización."
        ),
    },
    {
        "nombre": "Desayuno amoroso para mamá",
        "precio": "75000.00",
        "imagen": "productos/mujer/desayuno-amoroso-mama-20260514.jpeg",
        "descripcion": (
            "Desayuno en caja de madera con decoración de globos, mix de frutas, "
            "yogurt, sándwich de tocineta, doble queso y lechuga, más decoración "
            "especial para sorprender a mamá. Precio base sujeto a personalización."
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
                "imagen": item["imagen"],
                "destacado": False,
            },
        )


def remove_breakfast_products(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre__in=[item["nombre"] for item in PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0023_seed_mujer_mayo_products"),
    ]

    operations = [
        migrations.RunPython(add_breakfast_products, remove_breakfast_products),
    ]
