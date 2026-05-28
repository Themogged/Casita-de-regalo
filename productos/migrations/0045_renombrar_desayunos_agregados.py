from django.db import migrations


NAME_CHANGES = [
    {
        "imagen": "productos/desayunos/desayuno-cajita-feliz-20260528.jpeg",
        "nuevo": "Desayuno caja en acetato",
        "anterior": "Desayuno",
    },
    {
        "imagen": "productos/desayunos/desayuno-mesa-madera-hatsu-20260528.jpeg",
        "nuevo": "Desayuno mesa con arco",
        "anterior": "Desayuno",
    },
    {
        "imagen": "productos/desayunos/desayuno-cajita-sorpresa-feliz-dia-20260528.jpeg",
        "nuevo": "Desayuno cajita feliz",
        "anterior": "Desayuno cajita feliz",
    },
    {
        "imagen": "productos/desayunos/desayuno-cumpleanos-con-luces-20260528.jpeg",
        "nuevo": "Desayuno cumpleaños con luces",
        "anterior": "Desayuno",
    },
    {
        "imagen": "productos/desayunos/desayuno-tocador-20260528.jpeg",
        "nuevo": "Desayuno tocador con flores",
        "anterior": "Desayuno tocador",
    },
]


def _rename_products(apps, direction):
    Producto = apps.get_model("productos", "Producto")

    for item in NAME_CHANGES:
        Producto.objects.filter(imagen=item["imagen"]).update(nombre=item[direction])


def apply_name_changes(apps, schema_editor):
    _rename_products(apps, "nuevo")


def restore_previous_names(apps, schema_editor):
    _rename_products(apps, "anterior")


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0044_ajustar_desayuno_caja_carton_acetato"),
    ]

    operations = [
        migrations.RunPython(apply_name_changes, restore_previous_names),
    ]
