from django.db import migrations


PRODUCT_NAME = "Desayuno cajita sorpresa"
GALLERY_IMAGE = "productos/desayunos/desayuno-cajita-sorpresa-feliz-dia-20260528.jpeg"


def add_breakfast_gallery_image(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    ProductoImagen = apps.get_model("productos", "ProductoImagen")

    producto = Producto.objects.filter(nombre=PRODUCT_NAME).first()
    if not producto:
        return

    ProductoImagen.objects.update_or_create(
        producto=producto,
        orden=1,
        defaults={
            "imagen": GALLERY_IMAGE,
            "titulo": "Vista Feliz día",
        },
    )


def remove_breakfast_gallery_image(apps, schema_editor):
    ProductoImagen = apps.get_model("productos", "ProductoImagen")
    ProductoImagen.objects.filter(imagen=GALLERY_IMAGE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0039_renombrar_desayunos_recientes"),
    ]

    operations = [
        migrations.RunPython(add_breakfast_gallery_image, remove_breakfast_gallery_image),
    ]
