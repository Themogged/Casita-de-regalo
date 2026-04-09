from django.db import migrations


OLD_NAME = "Sorpresa infantil Huntrix"
NEW_NAME = "Sorpresa infantil Guerreras Kpop"

NEW_DESCRIPTION = (
    "Caja infantil inspirada en guerreras k-pop, pensada para celebraciones con una presentación abundante y llamativa.\n\n"
    "Incluye:\n"
    "- caja y espaldar de madera\n"
    "- globos\n"
    "- decoración\n"
    "- gomitas\n"
    "- crispetas\n"
    "- papas\n"
    "- deditos de chocolate\n"
    "- cereales\n"
    "- bombones\n"
    "- gelatina\n"
    "- fruta\n"
    "- cajitas de refresco Hit\n\n"
    "Se puede ajustar con personaje, nombre y detalles que el cliente desee."
)


OLD_DESCRIPTION = (
    "Caja infantil con temática Huntrix, pensada para celebraciones con una presentación abundante y llamativa.\n\n"
    "Incluye:\n"
    "- caja y espaldar de madera\n"
    "- globos\n"
    "- decoración\n"
    "- gomitas\n"
    "- crispetas\n"
    "- papas\n"
    "- deditos de chocolate\n"
    "- cereales\n"
    "- bombones\n"
    "- gelatina\n"
    "- fruta\n"
    "- cajitas de refresco Hit\n\n"
    "Se puede ajustar con personaje, nombre y detalles que el cliente desee."
)


def rename_product(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=OLD_NAME).update(nombre=NEW_NAME, descripcion=NEW_DESCRIPTION)


def revert_product(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre=NEW_NAME).update(nombre=OLD_NAME, descripcion=OLD_DESCRIPTION)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0013_renombrar_huntrix"),
    ]

    operations = [
        migrations.RunPython(rename_product, revert_product),
    ]
