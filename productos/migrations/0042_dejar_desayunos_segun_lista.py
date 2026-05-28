from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Cumpleaños y desayunos"

BREAKFASTS = [
    {
        "match_images": ["productos/desayunos/desayuno-tocador-20260528.jpeg"],
        "nombre": "Desayuno tocador",
        "precio": "168000.00",
        "descripcion": (
            "Tocador en madera, jugo, mix de fruta, waffles con queso y fruta, "
            "ramo de flores."
        ),
        "previous_name": "Desayuno tocador",
    },
    {
        "match_images": ["productos/desayunos/desayuno-mesa-madera-hatsu-20260528.jpeg"],
        "nombre": "Desayuno",
        "precio": "70000.00",
        "descripcion": (
            "Mesa de desayuno en madera con arco de globos y flores, mix de frutas, "
            "manzana, pera, té Hatsu y decoración."
        ),
        "previous_name": "Desayuno mesa en madera",
    },
    {
        "match_images": ["productos/desayunos/desayuno-cajita-feliz-20260528.jpeg"],
        "nombre": "Desayuno cajita feliz",
        "precio": "63000.00",
        "descripcion": (
            "Caja en cartón con creps de pollo y verduras, mix de fruta, jugo, "
            "globo, pin decorativo y decoración."
        ),
        "previous_name": "Desayuno cajita feliz",
    },
    {
        "match_images": ["productos/desayunos/desayuno-cumpleanos-con-luces-20260528.jpeg"],
        "nombre": "Desayuno",
        "precio": "140000.00",
        "descripcion": (
            "Caja en madera con espaldar, flores, Milo, Bonyurt, waffles con fresas, "
            "cupcake, pocillo, mix de frutas, pin decorativo, decoración y luces."
        ),
        "previous_name": "Desayuno con espaldar y luces",
    },
]


def _sync_breakfasts(apps, names_from_field):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)

    for item in BREAKFASTS:
        producto = None
        for image_path in item["match_images"]:
            producto = Producto.objects.filter(imagen=image_path).first()
            if producto:
                break

        if not producto:
            producto = Producto.objects.filter(nombre=item[names_from_field]).first()

        if not producto:
            continue

        producto.nombre = item[names_from_field]
        producto.descripcion = item["descripcion"]
        producto.precio = Decimal(item["precio"])
        producto.stock = 100
        producto.categoria = categoria
        producto.destacado = False
        producto.save(
            update_fields=[
                "nombre",
                "descripcion",
                "precio",
                "stock",
                "categoria",
                "destacado",
            ]
        )


def apply_breakfasts_from_user_list(apps, schema_editor):
    _sync_breakfasts(apps, "nombre")


def restore_previous_breakfast_names(apps, schema_editor):
    _sync_breakfasts(apps, "previous_name")


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0041_ajustar_nombres_desayunos_segun_lista"),
    ]

    operations = [
        migrations.RunPython(apply_breakfasts_from_user_list, restore_previous_breakfast_names),
    ]
