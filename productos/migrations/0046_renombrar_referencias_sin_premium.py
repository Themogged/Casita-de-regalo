from django.db import migrations


PRODUCT_CHANGES = [
    {
        "anterior": "Cumple azul premium",
        "nuevo": "Cumple azul en madera",
        "descripcion": (
            "Referencia con caja en madera, globos, mix de fruta, waffles, jugo "
            "y decoración para celebrar con tono elegante."
        ),
    },
    {
        "anterior": "Rosas y fresas premium",
        "nuevo": "Rosas y fresas especiales",
        "descripcion": (
            "Propuestas con rosas, fresas cubiertas, licor y presentaciones cuidadas "
            "para sorprender con alto impacto."
        ),
    },
    {
        "anterior": "Black and gold deluxe",
        "nuevo": "Black and gold deluxe",
        "descripcion": (
            "Detalle con globos negro y dorado, fruta, cereal y una presentación "
            "más sofisticada."
        ),
    },
    {
        "anterior": "Caja corazón premium",
        "nuevo": "Caja corazón especial",
        "descripcion": (
            "Caja fina en forma de corazón con sándwich, jugo, rosas, chocolates "
            "o peluche para un detalle romántico."
        ),
    },
    {
        "anterior": "Referencia para hombres premium",
        "nuevo": "Referencia para hombres",
        "descripcion": (
            "Detalle pensado para hombres, con presentación sobria, snacks y acabados "
            "personalizados según la ocasión."
        ),
    },
    {
        "anterior": "Cumple cerdita premium",
        "nuevo": "Cumple cerdita especial",
        "descripcion": (
            "Detalle temático de cumpleaños con decoración infantil, color y acabados "
            "personalizados."
        ),
    },
    {
        "anterior": "Desayuno infantil premium en mesa",
        "nuevo": "Desayuno infantil en mesa",
        "descripcion": (
            "Desayuno infantil en mesa con decoración temática, alimentos surtidos "
            "y presentación personalizada."
        ),
    },
]


def apply_name_changes(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    for item in PRODUCT_CHANGES:
        Producto.objects.filter(nombre=item["anterior"]).update(
            nombre=item["nuevo"],
            descripcion=item["descripcion"],
        )


def restore_previous_names(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    for item in PRODUCT_CHANGES:
        Producto.objects.filter(nombre=item["nuevo"]).update(nombre=item["anterior"])


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0045_renombrar_desayunos_agregados"),
    ]

    operations = [
        migrations.RunPython(apply_name_changes, restore_previous_names),
    ]
