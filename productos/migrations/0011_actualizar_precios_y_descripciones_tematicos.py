from django.db import migrations


UPDATES = {
    "Pocoyó frutal infantil": {
        "precio": "97000.00",
    },
    "Temático Stitch personalizado": {
        "precio": "25000.00",
        "descripcion": (
            "Referencia infantil en tonos azules para personalizar con Stitch u otro personaje favorito. "
            "Perfecta para armar con dulces, sorpresas o recordatorios según el presupuesto del cliente. "
            "Se le agrega lo que el cliente desee o pida a elección."
        ),
    },
    "Temático Pitufos personalizado": {
        "precio": "25000.00",
        "descripcion": (
            "Ejemplo de detalle temático con estructura decorativa ligera y presentación infantil. "
            "Se adapta a nombre, personaje, colores y contenido elegido por el cliente. "
            "Se le agrega lo que el cliente desee o pida a elección."
        ),
    },
    "Cumple temático Barbie": {
        "precio": "25000.00",
        "descripcion": (
            "Diseño rosado para cumpleaños infantiles inspirado en Barbie o estilos princesa. "
            "Ideal para personalizar con nombre, edad, snacks, decoración y mensaje especial. "
            "Se le agrega lo que el cliente desee o pida a elección."
        ),
    },
    "Cumple temático Hello Kitty": {
        "precio": "25000.00",
        "descripcion": (
            "Detalle infantil con estética dulce y femenina, perfecto para fiestas de Hello Kitty. "
            "El cliente puede elegir nombre, edad, colores pastel y el tipo de relleno. "
            "Se le agrega lo que el cliente desee o pida a elección."
        ),
    },
}


OLD_VALUES = {
    "Pocoyó frutal infantil": {
        "precio": "55000.00",
    },
    "Temático Stitch personalizado": {
        "precio": "42000.00",
        "descripcion": (
            "Referencia infantil en tonos azules para personalizar con Stitch u otro personaje favorito. "
            "Perfecta para armar con dulces, sorpresas o recordatorios según el presupuesto del cliente."
        ),
    },
    "Temático Pitufos personalizado": {
        "precio": "42000.00",
        "descripcion": (
            "Ejemplo de detalle temático con estructura decorativa ligera y presentación infantil. "
            "Se adapta a nombre, personaje, colores y contenido elegido por el cliente."
        ),
    },
    "Cumple temático Barbie": {
        "precio": "42000.00",
        "descripcion": (
            "Diseño rosado para cumpleaños infantiles inspirado en Barbie o estilos princesa. "
            "Ideal para personalizar con nombre, edad, snacks, decoración y mensaje especial."
        ),
    },
    "Cumple temático Hello Kitty": {
        "precio": "42000.00",
        "descripcion": (
            "Detalle infantil con estética dulce y femenina, perfecto para fiestas de Hello Kitty. "
            "El cliente puede elegir nombre, edad, colores pastel y el tipo de relleno."
        ),
    },
}


def apply_updates(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    for nombre, changes in UPDATES.items():
        Producto.objects.filter(nombre=nombre).update(**changes)


def revert_updates(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    for nombre, changes in OLD_VALUES.items():
        Producto.objects.filter(nombre=nombre).update(**changes)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0010_eliminar_tematico_personalizado"),
    ]

    operations = [
        migrations.RunPython(apply_updates, revert_updates),
    ]
