from django.db import migrations


PRODUCT_NAME = "Desayuno cumpleaños con luces"
IMAGE_PATH = "productos/desayunos/desayuno-cumpleanos-con-luces-20260528.jpeg"


def add_breakfast_image(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).update(imagen=IMAGE_PATH)


def remove_breakfast_image(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).update(imagen="")


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0034_agregar_desayuno_cumpleanos_luces"),
    ]

    operations = [
        migrations.RunPython(add_breakfast_image, remove_breakfast_image),
    ]
