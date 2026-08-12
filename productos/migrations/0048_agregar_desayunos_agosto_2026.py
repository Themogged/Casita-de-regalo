from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Cumpleaños y desayunos"

BREAKFASTS = (
    {
        "nombre": "Super desayuno",
        "descripcion": (
            "Caja exagonal en madera con globos en latex, yogurt, jugo de naranja, "
            "mix de fruta, wafles con queso, fresas y miel, frasco con cereal, postre, "
            "alpinette, frasquito con miel y frasquito con dulces, servilletas, "
            "cubiertos, decoración y tarjeta."
        ),
        "precio": "125000.00",
        "imagen": "productos/desayunos/super-desayuno-20260812.jpeg",
    },
    {
        "nombre": "Desayuno corazón",
        "descripcion": (
            "Caja fina, rosas, sanduche jamón, queso y lechuga, mix de fruta, porción "
            "de torta, jugo naranja, café capuchino, tarjeta, servilletas, cubiertos y decoración."
        ),
        "precio": "124000.00",
        "imagen": "productos/desayunos/desayuno-corazon-20260812.jpeg",
    },
)


def add_august_breakfasts(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    category, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    for breakfast in BREAKFASTS:
        Producto.objects.update_or_create(
            imagen=breakfast["imagen"],
            defaults={
                "nombre": breakfast["nombre"],
                "descripcion": breakfast["descripcion"],
                "precio": Decimal(breakfast["precio"]),
                "stock": 100,
                "categoria": category,
                "destacado": False,
            },
        )


def remove_august_breakfasts(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(imagen__in=[item["imagen"] for item in BREAKFASTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0047_validate_video_content"),
    ]

    operations = [
        migrations.RunPython(add_august_breakfasts, remove_august_breakfasts),
    ]
