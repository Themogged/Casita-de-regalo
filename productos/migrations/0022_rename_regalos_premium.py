from django.db import migrations


OLD_NAME = "Regalos premium"
NEW_NAME = "Detalles especiales"


def rename_regalos_premium(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Categoria.objects.filter(nombre=OLD_NAME).update(nombre=NEW_NAME)


def restore_regalos_premium(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Categoria.objects.filter(nombre=NEW_NAME).update(nombre=OLD_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0021_seed_segment_reference_products"),
    ]

    operations = [
        migrations.RunPython(rename_regalos_premium, restore_regalos_premium),
    ]
