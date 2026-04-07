from django.db import migrations


def fix_birthday_category(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    nueva, _ = Categoria.objects.get_or_create(nombre="Cumpleaños y desayunos")
    antigua = Categoria.objects.filter(nombre="Cumpleanos y desayunos").first()

    if antigua and antigua.id != nueva.id:
        Producto.objects.filter(categoria=antigua).update(categoria=nueva)
        antigua.delete()


def revert_birthday_category(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    antigua, _ = Categoria.objects.get_or_create(nombre="Cumpleanos y desayunos")
    nueva = Categoria.objects.filter(nombre="Cumpleaños y desayunos").first()

    if nueva and nueva.id != antigua.id:
        Producto.objects.filter(categoria=nueva).update(categoria=antigua)
        nueva.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0004_expandir_tematicos_infantiles"),
    ]

    operations = [
        migrations.RunPython(fix_birthday_category, revert_birthday_category),
    ]
