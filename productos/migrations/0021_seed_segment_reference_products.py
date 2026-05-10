from decimal import Decimal

from django.db import migrations


REFERENCE_PRODUCTS = [
    {
        "categoria": "Para hombres",
        "nombre": "Referencia para hombres premium",
        "fuente": "Black and gold deluxe",
        "precio": "94000.00",
        "descripcion": (
            "Detalle de referencia para cotizar opciones sobrias, snacks, globos "
            "y acabados elegantes para cumpleaños, aniversario o sorpresa especial."
        ),
    },
    {
        "categoria": "Para mujer",
        "nombre": "Referencia especial para mujer",
        "fuente": "Desayuno mariposa rosa",
        "precio": "89000.00",
        "descripcion": (
            "Propuesta de referencia para detalles femeninos con colores suaves, "
            "decoración cuidada y selección personalizada según la ocasión."
        ),
    },
    {
        "categoria": "Niños",
        "nombre": "Referencia infantil personalizada",
        "fuente": "Caja temática Toy Story",
        "precio": "70000.00",
        "descripcion": (
            "Referencia temática infantil para cotizar personajes, colores, dulces "
            "y decoración a elección del cliente."
        ),
    },
    {
        "categoria": "Amor y aniversario",
        "nombre": "Referencia aniversario romántica",
        "fuente": "Caja aniversario te amo",
        "precio": "75000.00",
        "descripcion": (
            "Detalle de referencia para aniversarios, fechas románticas y sorpresas "
            "con mensaje personalizado, globos y presentación especial."
        ),
    },
    {
        "categoria": "Amor y aniversario",
        "nombre": "Referencia ancheta de amor",
        "fuente": "Caja corazón premium",
        "precio": "122000.00",
        "descripcion": (
            "Ancheta de referencia para detalles de amor con caja decorada, dulces, "
            "flores o complementos elegidos según el estilo de la sorpresa."
        ),
    },
]


def _field_file_name(value):
    return getattr(value, "name", value) or ""


def create_reference_products(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    for item in REFERENCE_PRODUCTS:
        categoria, _ = Categoria.objects.get_or_create(nombre=item["categoria"])
        fuente = Producto.objects.filter(nombre=item["fuente"]).first()
        imagen = _field_file_name(fuente.imagen) if fuente else ""
        precio = fuente.precio if fuente else Decimal(item["precio"])

        Producto.objects.update_or_create(
            nombre=item["nombre"],
            defaults={
                "descripcion": item["descripcion"],
                "precio": precio,
                "stock": 100,
                "categoria": categoria,
                "imagen": imagen,
                "destacado": False,
            },
        )


def remove_reference_products(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(
        nombre__in=[item["nombre"] for item in REFERENCE_PRODUCTS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0020_seed_segment_categories"),
    ]

    operations = [
        migrations.RunPython(create_reference_products, remove_reference_products),
    ]
