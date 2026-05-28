from django.db import migrations


RENAMES = {
    "Desayuno arco frutal": "Desayuno mesa en madera",
    "Desayuno cajita sorpresa": "Desayuno cajita feliz",
    "Desayuno de cumpleaños con luces": "Desayuno con espaldar y luces",
    "Desayuno floral en tocador": "Desayuno tocador",
}


def apply_breakfast_names(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    for old_name, new_name in RENAMES.items():
        Producto.objects.filter(nombre=old_name).update(nombre=new_name)


def restore_breakfast_names(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    for old_name, new_name in RENAMES.items():
        Producto.objects.filter(nombre=new_name).update(nombre=old_name)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0040_agregar_galeria_desayuno_cajita_sorpresa"),
    ]

    operations = [
        migrations.RunPython(apply_breakfast_names, restore_breakfast_names),
    ]
