from django.db import migrations


THEMATIC_PRODUCTS = [
    {
        "nombre": "Tem\u00e1tico personalizado a elecci\u00f3n",
        "legacy_names": ["Tematicos con personaje"],
        "descripcion": (
            "Dise\u00f1o tem\u00e1tico infantil personalizable con personaje, colores, nombre y mensaje del cliente. "
            "Ideal para ideas como Hello Kitty, Mario, Stitch, Pitufos y m\u00e1s. "
            "El valor final puede variar seg\u00fan el contenido, tama\u00f1o y nivel de decoraci\u00f3n."
        ),
        "precio": "44000.00",
        "stock": 6,
        "imagen": "referencias/referencia-11.png",
        "destacado": True,
    },
    {
        "nombre": "Detalle Bob Esponja infantil",
        "descripcion": (
            "Detalle tem\u00e1tico inspirado en Bob Esponja, ideal para regalos infantiles llenos de color y dulces.\n\n"
            "Incluye:\n"
            "- cajas en icopor y cart\u00f3n\n"
            "- decoraci\u00f3n\n"
            "- tarjeta\n"
            "- 6 paquetes de gomas Trululu\n"
            "- 3 cajitas de bebida Milo\n"
            "- 3 galletas Milo\n"
            "- 2 mini chocolatinas Hershey\n"
            "- 1 Jumbo Man\u00ed mediano\n"
            "- 2 chocolatinas Jet\n\n"
            "Se puede personalizar con nombre, colores y acabados seg\u00fan la ocasi\u00f3n."
        ),
        "precio": "65000.00",
        "stock": 5,
        "imagen": "productos/tematicos/bob-esponja-20260406.jpeg",
        "destacado": True,
    },
    {
        "nombre": "Caja tem\u00e1tica Toy Story",
        "descripcion": (
            "Caja tem\u00e1tica de Toy Story con montaje llamativo para cumplea\u00f1os infantiles.\n\n"
            "Incluye:\n"
            "- caja de madera pintada\n"
            "- globos\n"
            "- tarjeta\n"
            "- decoraci\u00f3n\n"
            "- 2 Cheetos\n"
            "- 2 Ponky\n"
            "- 2 Mini Chisp\n"
            "- 2 galletas Noel Wafer\n"
            "- 2 gelatinas\n"
            "- 2 yogures\n\n"
            "Se puede personalizar con nombre y edad del cumplea\u00f1ero."
        ),
        "precio": "70000.00",
        "stock": 5,
        "imagen": "productos/tematicos/toy-story.jpeg",
        "destacado": True,
    },
    {
        "nombre": "Tem\u00e1tico Stitch personalizado",
        "descripcion": (
            "Referencia infantil en tonos azules para personalizar con Stitch u otro personaje favorito. "
            "Perfecta para armar con dulces, sorpresas o recordatorios seg\u00fan el presupuesto del cliente."
        ),
        "precio": "42000.00",
        "stock": 6,
        "imagen": "productos/tematicos/stitch.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Tem\u00e1tico Pitufos personalizado",
        "descripcion": (
            "Ejemplo de detalle tem\u00e1tico con estructura decorativa ligera y presentaci\u00f3n infantil. "
            "Se adapta a nombre, personaje, colores y contenido elegido por el cliente."
        ),
        "precio": "42000.00",
        "stock": 6,
        "imagen": "productos/tematicos/pitufos.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Cumple tem\u00e1tico Barbie",
        "descripcion": (
            "Dise\u00f1o rosado para cumplea\u00f1os infantiles inspirado en Barbie o estilos princesa. "
            "Ideal para personalizar con nombre, edad, snacks, decoraci\u00f3n y mensaje especial."
        ),
        "precio": "42000.00",
        "stock": 6,
        "imagen": "productos/tematicos/barbie.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Cumple tem\u00e1tico Hello Kitty",
        "descripcion": (
            "Detalle infantil con est\u00e9tica dulce y femenina, perfecto para fiestas de Hello Kitty. "
            "El cliente puede elegir nombre, edad, colores pastel y el tipo de relleno."
        ),
        "precio": "42000.00",
        "stock": 6,
        "imagen": "productos/tematicos/hello-kitty.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Pocoy\u00f3 frutal infantil",
        "descripcion": (
            "Modelo infantil con presentaci\u00f3n frutal, pensado para una opci\u00f3n fresca y colorida. "
            "Puede llevar frutas, decoraci\u00f3n tem\u00e1tica, nombre y contenido personalizado seg\u00fan la ocasi\u00f3n."
        ),
        "precio": "55000.00",
        "stock": 5,
        "imagen": "productos/tematicos/pocoyo.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Detalle Spider-Man snack",
        "descripcion": (
            "Detalle tem\u00e1tico inspirado en Spider-Man, ideal para cumplea\u00f1os infantiles con una presentaci\u00f3n compacta y llamativa.\n\n"
            "Incluye:\n"
            "- caja de cart\u00f3n\n"
            "- globos\n"
            "- tarjeta\n"
            "- decoraci\u00f3n\n"
            "- gomas Trolli\n"
            "- galletas Nucita\n"
            "- chocolatina Jet Wafer\n"
            "- chocolates Bianchi\n"
            "- paleta coraz\u00f3n\n\n"
            "Se puede ajustar con nombre, edad y colores del montaje."
        ),
        "precio": "49000.00",
        "stock": 5,
        "imagen": "productos/tematicos/spiderman.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Cumple cerdita premium",
        "descripcion": (
            "Detalle tierno de cumplea\u00f1os con tem\u00e1tica de cerdita, pensado para celebraciones especiales con presentaci\u00f3n m\u00e1s completa.\n\n"
            "Incluye:\n"
            "- caja hexagonal de madera con espaldar de madera\n"
            "- globos\n"
            "- tarjeta\n"
            "- decoraci\u00f3n\n"
            "- stickers de Feliz Cumplea\u00f1os\n"
            "- peluche\n"
            "- mix de fruta\n"
            "- gomas Trolli\n"
            "- Bon Yurt\n"
            "- Alpinito\n"
            "- mini torta\n"
            "- Cheesetris\n\n"
            "Ideal para personalizar con nombre y detalles del festejo."
        ),
        "precio": "115000.00",
        "stock": 4,
        "imagen": "productos/tematicos/cerdita.jpeg",
        "destacado": True,
    },
    {
        "nombre": "Caja hexagonal Ma\u00f1ana ser\u00e1 bonito",
        "descripcion": (
            "Caja de estilo pastel con presentaci\u00f3n hexagonal y mensaje protagonista, perfecta para regalos dulces y personalizados.\n\n"
            "Incluye:\n"
            "- caja en madera\n"
            "- espaldar en madera\n"
            "- globos\n"
            "- tarjeta\n"
            "- decoraci\u00f3n\n"
            "- mini torta\n"
            "- gomas Trululu\n"
            "- masmelos\n"
            "- mentas\n\n"
            "Funciona muy bien para cumplea\u00f1os, sorpresas y detalles personalizados con un look delicado."
        ),
        "precio": "70000.00",
        "stock": 4,
        "imagen": "productos/tematicos/manana-sera-bonito.jpeg",
        "destacado": False,
    },
    {
        "nombre": "Unicornio pony sorpresa",
        "descripcion": (
            "Detalle infantil en tonos pastel con tem\u00e1tica de unicornio y pony, pensado para sorprender con un regalo m\u00e1s completo.\n\n"
            "Incluye:\n"
            "- caja en madera pintada\n"
            "- decoraci\u00f3n de globos\n"
            "- globo burbuja\n"
            "- postre en copa\n"
            "- Bianchi\n"
            "- masmelos\n"
            "- decoraci\u00f3n\n"
            "- tarjeta\n"
            "- regalo de pony\n"
            "- cartuchera\n"
            "- naranja\n\n"
            "Se puede personalizar con nombre, edad y paleta de color."
        ),
        "precio": "83000.00",
        "stock": 4,
        "imagen": "productos/tematicos/unicornio-pony.jpeg",
        "destacado": False,
    },
]


def seed_thematic_products(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria = Categoria.objects.filter(nombre="Tem\u00e1ticos e infantiles").first()
    if categoria is None:
        categoria = Categoria.objects.filter(nombre="Tematicos e infantiles").first()

    if categoria is None:
        categoria = Categoria.objects.create(nombre="Tem\u00e1ticos e infantiles")
    elif categoria.nombre != "Tem\u00e1ticos e infantiles":
        categoria.nombre = "Tem\u00e1ticos e infantiles"
        categoria.save(update_fields=["nombre"])

    for item in THEMATIC_PRODUCTS:
        legacy_names = item.get("legacy_names", [])
        producto = None

        for candidate in [item["nombre"], *legacy_names]:
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


def unseed_thematic_products(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    names = [item["nombre"] for item in THEMATIC_PRODUCTS]
    Producto.objects.filter(nombre__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0003_productoimagen"),
    ]

    operations = [
        migrations.RunPython(seed_thematic_products, unseed_thematic_products),
    ]
