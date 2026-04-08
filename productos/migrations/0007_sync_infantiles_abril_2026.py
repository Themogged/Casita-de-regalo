from django.db import migrations


INFANTILE_PRODUCTS = [
    {
        "nombre": "Cumple Catnap snack",
        "legacy_names": ["Cumple gatita lunar snack"],
        "descripcion": (
            "Contiene:\n"
            "- caja de madera pintada\n"
            "- globos\n"
            "- tarjeta\n"
            "- decoración\n"
            "- Trululu gomas\n"
            "- Takis\n"
            "- bebida Alpin"
        ),
        "precio": "150000.00",
        "stock": 4,
        "imagen": "productos/tematicos/gatita-lunar-cumple-20260408.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Caja Spider-Man mediana",
        "descripcion": (
            "Contiene:\n"
            "- caja en madera mediana\n"
            "- decoración con globos\n"
            "- masmelos\n"
            "- chocolatina Hershey\n"
            "- Trululu\n"
            "- chocolatinas\n"
            "- decoración\n"
            "- tarjeta"
        ),
        "precio": "59000.00",
        "stock": 5,
        "imagen": "productos/tematicos/spiderman-caja-mediana-20260408.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Ramo en papel coreano con peluche",
        "descripcion": (
            "Contiene:\n"
            "- ramo en papel coreano\n"
            "- peluche\n"
            "- flores artificiales (si las quiere naturales, el precio varía)\n"
            "- oasis\n"
            "- moño\n"
            "- tarjeta"
        ),
        "precio": "87000.00",
        "stock": 4,
        "imagen": "productos/tematicos/ramo-coreano-peluche-20260408.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Caja Stitch cumpleaños deluxe",
        "descripcion": (
            "Esta contiene:\n"
            "- caja en madera\n"
            "- arco de cumpleaños en madera\n"
            "- globos\n"
            "- luces\n"
            "- globo burbuja decorado\n"
            "- peluche\n"
            "- termo\n"
            "- reloj\n"
            "- papas Margarita\n"
            "- Cheetos\n"
            "- Doritos\n"
            "- huevos de chocolate\n"
            "- decoración\n"
            "- tarjeta"
        ),
        "precio": "172000.00",
        "stock": 3,
        "imagen": "productos/tematicos/stitch-cumple-deluxe-20260408.jpeg",
        "destacado": True,
    },
    {
        "nombre": "Desayuno infantil premium en mesa",
        "descripcion": (
            "Contiene:\n"
            "- mesa y espaldar en madera pintada\n"
            "- globos\n"
            "- luces\n"
            "- stickers\n"
            "- peluche (consultar disponibilidad)\n"
            "- yogurt\n"
            "- jugo\n"
            "- mix de frutas\n"
            "- galletas en recipiente de corazón\n"
            "- wafles con fresas\n"
            "- frasquito con gomitas\n"
            "- frasquito con chocolates\n"
            "- decoración\n"
            "- tarjeta\n\n"
            "Incluye una foto principal y una imagen adicional de referencia."
        ),
        "precio": "137000.00",
        "stock": 3,
        "imagen": "productos/tematicos/desayuno-infantil-mesa-20260408.jpeg",
        "destacado": True,
    },
]


REFRESH_IMAGE_PATHS = {
    "Caja temática Toy Story": "productos/tematicos/toy-story-correcto-20260408.jpeg",
    "Pocoyó frutal infantil": "productos/tematicos/pocoyo-correcto-20260408.jpeg",
}


ORIGINAL_IMAGE_PATHS = {
    "Caja temática Toy Story": "productos/tematicos/toy-story.jpeg",
    "Pocoyó frutal infantil": "productos/tematicos/pocoyo.jpeg",
}


GALLERY_ITEMS = [
    {
        "producto": "Desayuno infantil premium en mesa",
        "imagen": "productos/tematicos/desayuno-infantil-mesa-ref-20260408.jpeg",
        "titulo": "Referencia adicional",
        "orden": 1,
    }
]


def _get_infantile_category(Categoria):
    categoria = Categoria.objects.filter(nombre="Temáticos e infantiles").first()
    if categoria is None:
        categoria = Categoria.objects.filter(nombre="Tematicos e infantiles").first()

    if categoria is None:
        categoria = Categoria.objects.create(nombre="Temáticos e infantiles")
    elif categoria.nombre != "Temáticos e infantiles":
        categoria.nombre = "Temáticos e infantiles"
        categoria.save(update_fields=["nombre"])

    return categoria


def sync_infantile_catalog(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    ProductoImagen = apps.get_model("productos", "ProductoImagen")

    categoria = _get_infantile_category(Categoria)

    for item in INFANTILE_PRODUCTS:
        producto = None
        for candidate in [item["nombre"], *item.get("legacy_names", [])]:
            producto = Producto.objects.filter(nombre=candidate).first()
            if producto:
                break

        defaults = {
            "descripcion": item["descripcion"],
            "precio": item["precio"],
            "stock": item["stock"],
            "categoria": categoria,
            "imagen": item["imagen"],
            "destacado": item["destacado"],
        }

        if producto:
            producto.nombre = item["nombre"]
            for field, value in defaults.items():
                setattr(producto, field, value)
            producto.save()
        else:
            Producto.objects.create(nombre=item["nombre"], **defaults)

    for product_name, image_path in REFRESH_IMAGE_PATHS.items():
        Producto.objects.filter(nombre=product_name).update(imagen=image_path)

    for item in GALLERY_ITEMS:
        producto = Producto.objects.filter(nombre=item["producto"]).first()
        if not producto:
            continue

        ProductoImagen.objects.update_or_create(
            producto=producto,
            orden=item["orden"],
            defaults={
                "imagen": item["imagen"],
                "titulo": item["titulo"],
            },
        )


def revert_infantile_catalog(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    ProductoImagen = apps.get_model("productos", "ProductoImagen")

    for item in GALLERY_ITEMS:
        ProductoImagen.objects.filter(imagen=item["imagen"]).delete()

    for product_name, image_path in ORIGINAL_IMAGE_PATHS.items():
        Producto.objects.filter(nombre=product_name).update(imagen=image_path)

    removable_names = []
    for item in INFANTILE_PRODUCTS:
        removable_names.append(item["nombre"])
        removable_names.extend(item.get("legacy_names", []))

    Producto.objects.filter(nombre__in=removable_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0006_actualizar_imagen_bob_esponja"),
    ]

    operations = [
        migrations.RunPython(sync_infantile_catalog, revert_infantile_catalog),
    ]
