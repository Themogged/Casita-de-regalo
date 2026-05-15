from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Para mujer"

PRODUCTS = [
    {
        "nombre": "Desayuno feliz día mamá",
        "precio": "110000.00",
        "imagen": "productos/mujer/desayuno-feliz-dia-mama-20260514.jpeg",
        "descripcion": (
            "Desayuno en caja hexagonal de madera con globos, jugo, yogurt, "
            "frasco con galletas, postre de tres leches con frosting de queso, "
            "mix de fruta, waffles con fresas, sándwich de jamón, queso, tocineta "
            "y lechuga, decoración y tarjeta. Precio base sujeto a disponibilidad "
            "de insumos y personalización."
        ),
    },
    {
        "nombre": "Desayuno para mamá premium",
        "precio": "130000.00",
        "imagen": "productos/mujer/desayuno-para-mama-premium-20260514.jpeg",
        "descripcion": (
            "Desayuno en caja de madera con espaldar pintado, arco de globos, "
            "globo burbuja, jugo, waffles con queso y fruta, mix de fruta, maní "
            "La Especial, chocolatina Jumbo mediana, mini cake y decoración. "
            "Precio base sujeto a disponibilidad de insumos y personalización."
        ),
    },
]


def add_premium_mom_breakfasts(apps, schema_editor):
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


def remove_premium_mom_breakfasts(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre__in=[item["nombre"] for item in PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0024_agregar_desayunos_mama_mujer"),
    ]

    operations = [
        migrations.RunPython(add_premium_mom_breakfasts, remove_premium_mom_breakfasts),
    ]
