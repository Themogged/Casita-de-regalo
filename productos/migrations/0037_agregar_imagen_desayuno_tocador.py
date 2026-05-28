from django.db import migrations


PRODUCT_NAME = "Desayuno tocador"
IMAGE_PATH = "productos/desayunos/desayuno-tocador-20260528.jpeg"


def add_dresser_breakfast_image(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).update(imagen=IMAGE_PATH)


def remove_dresser_breakfast_image(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=PRODUCT_NAME).update(imagen="")


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0036_agregar_desayuno_tocador"),
    ]

    operations = [
        migrations.RunPython(add_dresser_breakfast_image, remove_dresser_breakfast_image),
    ]
