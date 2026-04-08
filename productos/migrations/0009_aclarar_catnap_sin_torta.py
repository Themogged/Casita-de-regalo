from django.db import migrations


NEW_DESCRIPTION = (
    "Contiene:\n"
    "- caja de madera pintada\n"
    "- globos\n"
    "- tarjeta\n"
    "- decoraci\u00f3n\n"
    "- Trululu gomas\n"
    "- Takis\n"
    "- bebida Alpin\n\n"
    "La mini torta que aparece en la foto no est\u00e1 incluida."
)


OLD_DESCRIPTION = (
    "Contiene:\n"
    "- caja de madera pintada\n"
    "- globos\n"
    "- tarjeta\n"
    "- decoraci\u00f3n\n"
    "- Trululu gomas\n"
    "- Takis\n"
    "- bebida Alpin"
)


def set_catnap_description(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre="Cumple Catnap snack").update(descripcion=NEW_DESCRIPTION)


def revert_catnap_description(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre="Cumple Catnap snack").update(descripcion=OLD_DESCRIPTION)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0008_actualizar_precio_catnap"),
    ]

    operations = [
        migrations.RunPython(set_catnap_description, revert_catnap_description),
    ]
