from django.db import migrations


RENAMES = {
    "Desayuno": "Desayuno arco frutal",
    "Desayuno cajita feliz": "Desayuno cajita sorpresa",
    "Desayuno cumpleaños con luces": "Desayuno de cumpleaños con luces",
    "Desayuno tocador": "Desayuno floral en tocador",
}


def rename_recent_breakfasts(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    for old_name, new_name in RENAMES.items():
        Producto.objects.filter(nombre=old_name).update(nombre=new_name)


def restore_recent_breakfast_names(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    for old_name, new_name in RENAMES.items():
        Producto.objects.filter(nombre=new_name).update(nombre=old_name)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0038_agregar_imagenes_desayunos_generales"),
    ]

    operations = [
        migrations.RunPython(rename_recent_breakfasts, restore_recent_breakfast_names),
    ]
