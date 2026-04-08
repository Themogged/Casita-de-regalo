from django.db import migrations


REMOVED_NAMES = [
    "Temático personalizado a elección",
    "Tematicos con personaje",
]


def remove_thematic_product(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre__in=REMOVED_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0009_aclarar_catnap_sin_torta"),
    ]

    operations = [
        migrations.RunPython(remove_thematic_product, migrations.RunPython.noop),
    ]
