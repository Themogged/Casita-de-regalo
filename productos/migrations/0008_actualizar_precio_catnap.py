from django.db import migrations


def set_catnap_price(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre="Cumple Catnap snack").update(precio="73000.00")


def revert_catnap_price(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre="Cumple Catnap snack").update(precio="150000.00")


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0007_sync_infantiles_abril_2026"),
    ]

    operations = [
        migrations.RunPython(set_catnap_price, revert_catnap_price),
    ]
