from django.db import migrations


PRODUCT_IMAGES = {
    "Desayuno": "productos/desayunos/desayuno-mesa-madera-hatsu-20260528.jpeg",
    "Desayuno cajita feliz": "productos/desayunos/desayuno-cajita-feliz-20260528.jpeg",
}


def add_general_breakfast_images(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    for product_name, image_path in PRODUCT_IMAGES.items():
        Producto.objects.filter(nombre=product_name).update(imagen=image_path)


def remove_general_breakfast_images(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre__in=PRODUCT_IMAGES.keys()).update(imagen="")


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0037_agregar_imagen_desayuno_tocador"),
    ]

    operations = [
        migrations.RunPython(add_general_breakfast_images, remove_general_breakfast_images),
    ]
