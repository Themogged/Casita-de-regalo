from django.db import migrations


NEW_CATEGORIES = [
    "Para hombres",
    "Para mujer",
    "Niños",
]


def create_segment_categories(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    for name in NEW_CATEGORIES:
        Categoria.objects.get_or_create(nombre=name)


def remove_empty_segment_categories(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    for name in NEW_CATEGORIES:
        categoria = Categoria.objects.filter(nombre=name).first()
        if categoria and not categoria.producto_set.exists():
            categoria.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0019_alter_videoelaboracion_options_and_more"),
    ]

    operations = [
        migrations.RunPython(create_segment_categories, remove_empty_segment_categories),
    ]
