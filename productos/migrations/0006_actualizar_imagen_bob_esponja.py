from django.db import migrations


NEW_IMAGE_PATH = "productos/tematicos/bob-esponja-20260406.jpeg"
PRODUCT_NAME = "Detalle Bob Esponja infantil"


def update_bob_image(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).update(imagen=NEW_IMAGE_PATH)


def revert_bob_image(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).update(imagen="productos/tematicos/bob-esponja.jpeg")


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0005_corregir_categoria_cumpleanos"),
    ]

    operations = [
        migrations.RunPython(update_bob_image, revert_bob_image),
    ]
