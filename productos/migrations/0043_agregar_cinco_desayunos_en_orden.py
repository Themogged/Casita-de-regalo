from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Cumpleaños y desayunos"

ORDERED_BREAKFASTS = [
    {
        "nombre": "Desayuno tocador",
        "precio": "168000.00",
        "imagen": "productos/desayunos/desayuno-cajita-feliz-20260528.jpeg",
        "descripcion": (
            "Tocador en madera, jugo, mix de fruta, waffles con queso y fruta, "
            "ramo de flores."
        ),
    },
    {
        "nombre": "Desayuno",
        "precio": "70000.00",
        "imagen": "productos/desayunos/desayuno-mesa-madera-hatsu-20260528.jpeg",
        "descripcion": (
            "Mesa de desayuno en madera, arco con globos y flores, mix de frutas, "
            "manzana, pera, té Hatsu y decoración."
        ),
    },
    {
        "nombre": "Desayuno cajita feliz",
        "precio": "63000.00",
        "imagen": "productos/desayunos/desayuno-cajita-sorpresa-feliz-dia-20260528.jpeg",
        "descripcion": (
            "Caja en cartón, creps de pollo y verduras, mix de fruta, jugo, globo, "
            "pin decorativo y decoración."
        ),
    },
    {
        "nombre": "Desayuno",
        "precio": "140000.00",
        "imagen": "productos/desayunos/desayuno-cumpleanos-con-luces-20260528.jpeg",
        "descripcion": (
            "Caja en madera con espaldar, flores, Milo, Bonyurt, waffles con fresas, "
            "cupcake, pocillo, mix de frutas, pin decorativo, decoración y luces."
        ),
    },
    {
        "nombre": "Desayuno tocador",
        "precio": "168000.00",
        "imagen": "productos/desayunos/desayuno-tocador-20260528.jpeg",
        "descripcion": (
            "Tocador en madera, jugo, mix de fruta, waffles con queso y fruta, "
            "ramo de flores."
        ),
    },
]

PREVIOUS_BREAKFASTS = [
    {
        "nombre": "Desayuno cajita feliz",
        "precio": "63000.00",
        "imagen": "productos/desayunos/desayuno-cajita-feliz-20260528.jpeg",
        "descripcion": (
            "Caja en cartón con creps de pollo y verduras, mix de fruta, jugo, "
            "globo, pin decorativo y decoración."
        ),
    },
    {
        "nombre": "Desayuno",
        "precio": "70000.00",
        "imagen": "productos/desayunos/desayuno-mesa-madera-hatsu-20260528.jpeg",
        "descripcion": (
            "Mesa de desayuno en madera con arco de globos y flores, mix de frutas, "
            "manzana, pera, té Hatsu y decoración."
        ),
    },
    {
        "nombre": "Desayuno",
        "precio": "140000.00",
        "imagen": "productos/desayunos/desayuno-cumpleanos-con-luces-20260528.jpeg",
        "descripcion": (
            "Caja en madera con espaldar, flores, Milo, Bonyurt, waffles con fresas, "
            "cupcake, pocillo, mix de frutas, pin decorativo, decoración y luces."
        ),
    },
    {
        "nombre": "Desayuno tocador",
        "precio": "168000.00",
        "imagen": "productos/desayunos/desayuno-tocador-20260528.jpeg",
        "descripcion": (
            "Tocador en madera, jugo, mix de fruta, waffles con queso y fruta, "
            "ramo de flores."
        ),
    },
]

GALLERY_IMAGE = "productos/desayunos/desayuno-cajita-sorpresa-feliz-dia-20260528.jpeg"


def _sync_items(apps, items):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)

    for item in items:
        producto = Producto.objects.filter(imagen=item["imagen"]).first()
        if not producto:
            producto = Producto(imagen=item["imagen"])

        producto.nombre = item["nombre"]
        producto.descripcion = item["descripcion"]
        producto.precio = Decimal(item["precio"])
        producto.stock = 100
        producto.categoria = categoria
        producto.destacado = False
        producto.save()


def add_five_breakfasts_in_order(apps, schema_editor):
    ProductoImagen = apps.get_model("productos", "ProductoImagen")

    ProductoImagen.objects.filter(imagen=GALLERY_IMAGE).delete()
    _sync_items(apps, ORDERED_BREAKFASTS)


def restore_previous_breakfasts(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    ProductoImagen = apps.get_model("productos", "ProductoImagen")

    Producto.objects.filter(imagen=GALLERY_IMAGE).delete()
    _sync_items(apps, PREVIOUS_BREAKFASTS)

    gallery_product = Producto.objects.filter(
        imagen="productos/desayunos/desayuno-cajita-feliz-20260528.jpeg"
    ).first()
    if gallery_product:
        ProductoImagen.objects.update_or_create(
            producto=gallery_product,
            orden=1,
            defaults={
                "imagen": GALLERY_IMAGE,
                "titulo": "Vista Feliz día",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0042_dejar_desayunos_segun_lista"),
    ]

    operations = [
        migrations.RunPython(add_five_breakfasts_in_order, restore_previous_breakfasts),
    ]
