from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Para mujer"

PRODUCTS = [
    {
        "nombre": "Caja floral Amor de Mamá",
        "precio": "215000.00",
        "imagen": "productos/mujer/caja-floral-mama-premium-20260510.jpeg",
        "descripcion": (
            "Caja en madera con arco de globos, margaritas y rosas, chocolatina, "
            "paletas de caramelo, 18 Ferrero Rocher y decoración personalizada. "
            "Precio base sujeto a disponibilidad de flores e insumos."
        ),
    },
    {
        "nombre": "Desayuno Encanto de Mamá",
        "precio": "43000.00",
        "imagen": "productos/mujer/desayuno-dia-mama-sencillo-20260510.jpeg",
        "descripcion": (
            "Caja de cartón decorada con sánduche de jamón, queso y lechuga, "
            "mix de fruta, jugo de naranja y decoración especial."
        ),
    },
    {
        "nombre": "Desayuno Jardín de Abuelita",
        "precio": "125000.00",
        "imagen": "productos/mujer/desayuno-para-abuelita-deluxe-20260510.jpeg",
        "descripcion": (
            "Caja jardinera en madera con globos, globo personalizado, flores, bebida, "
            "sánduche doble de queso, jamón y lechuga, mix de fruta, cupcake, "
            "maní La Especial, chocolatina Hershey, chocolatina Golpe, Jumbito "
            "y decoración personalizada."
        ),
    },
]


def create_mujer_products(apps, schema_editor):
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


def remove_mujer_products(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre__in=[item["nombre"] for item in PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0022_rename_regalos_premium"),
    ]

    operations = [
        migrations.RunPython(create_mujer_products, remove_mujer_products),
    ]
