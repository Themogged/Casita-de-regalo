from django.db import migrations


NEW_PRODUCTS = [
    {
        "nombre": "Desayuno infantil futbolero",
        "descripcion": (
            "Desayuno infantil con temática futbolera, ideal para cumpleaños o sorpresas personalizadas.\n\n"
            "Incluye:\n"
            "- caja y espaldar en madera pintada\n"
            "- globos\n"
            "- sándwich de pollo y verduras\n"
            "- jugo de mora\n"
            "- galletas Club Social\n"
            "- decoración\n"
            "- tarjeta\n\n"
            "Se puede personalizar con nombre, edad y colores del montaje."
        ),
        "precio": "76000.00",
        "stock": 4,
        "imagen": "productos/tematicos/desayuno-futbolero-20260408.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Sorpresa infantil guerreras kpop",
        "descripcion": (
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
        ),
        "precio": "97000.00",
        "stock": 4,
        "imagen": "productos/tematicos/sorpresa-rosada-deluxe-20260408.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Cajitas infantiles personalizadas",
        "descripcion": (
            "Mini cajitas decoradas para detalles infantiles, ideales para fechas especiales, recordatorios o regalos rápidos.\n\n"
            "Incluyen:\n"
            "- cajitas en cartón decoradas\n"
            "- bebida a elección del cliente (jugo, yogurt, bebida de chocolate, leche o té)\n"
            "- cereal\n"
            "- galletas\n"
            "- chocolate\n\n"
            "Precio base desde 25.000 y se ajusta según el personaje, la bebida y los extras elegidos."
        ),
        "precio": "25000.00",
        "stock": 8,
        "imagen": "productos/tematicos/cajitas-infantiles-20260408.jpeg",
        "destacado": False,
    },
]


def add_new_infantile_products(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria = Categoria.objects.filter(nombre="Temáticos e infantiles").first()
    if categoria is None:
        categoria = Categoria.objects.filter(nombre="Tematicos e infantiles").first()

    if categoria is None:
        categoria = Categoria.objects.create(nombre="Temáticos e infantiles")
    elif categoria.nombre != "Temáticos e infantiles":
        categoria.nombre = "Temáticos e infantiles"
        categoria.save(update_fields=["nombre"])

    for item in NEW_PRODUCTS:
        Producto.objects.update_or_create(
            nombre=item["nombre"],
            defaults={
                "descripcion": item["descripcion"],
                "precio": item["precio"],
                "stock": item["stock"],
                "categoria": categoria,
                "imagen": item["imagen"],
                "destacado": item["destacado"],
            },
        )


def revert_new_infantile_products(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Producto.objects.filter(nombre__in=[item["nombre"] for item in NEW_PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0011_actualizar_precios_y_descripciones_tematicos"),
    ]

    operations = [
        migrations.RunPython(add_new_infantile_products, revert_new_infantile_products),
    ]
