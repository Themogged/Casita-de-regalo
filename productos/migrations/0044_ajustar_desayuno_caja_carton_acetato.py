from decimal import Decimal

from django.db import migrations


CATEGORY_NAME = "Cumpleaños y desayunos"
IMAGE_PATH = "productos/desayunos/desayuno-cajita-feliz-20260528.jpeg"

NEW_PRODUCT = {
    "nombre": "Desayuno",
    "precio": "143000.00",
    "descripcion": (
        "Caja cartón y en acetato, frasco con leche, frasco con yogurt, jugo, "
        "sándwich de jamón, queso y lechuga, waffles con queso y frutas, cereal, "
        "chocolatina Jumbo, chocolatina Hershey, mini cake y decoración."
    ),
}

PREVIOUS_PRODUCT = {
    "nombre": "Desayuno tocador",
    "precio": "168000.00",
    "descripcion": (
        "Tocador en madera, jugo, mix de fruta, waffles con queso y fruta, "
        "ramo de flores."
    ),
}


def _set_product(apps, product_data):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")

    categoria, _ = Categoria.objects.get_or_create(nombre=CATEGORY_NAME)
    producto = Producto.objects.filter(imagen=IMAGE_PATH).first()
    if not producto:
        producto = Producto(imagen=IMAGE_PATH)

    producto.nombre = product_data["nombre"]
    producto.descripcion = product_data["descripcion"]
    producto.precio = Decimal(product_data["precio"])
    producto.stock = 100
    producto.categoria = categoria
    producto.destacado = False
    producto.save()


def apply_product_update(apps, schema_editor):
    _set_product(apps, NEW_PRODUCT)


def restore_previous_product(apps, schema_editor):
    _set_product(apps, PREVIOUS_PRODUCT)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0043_agregar_cinco_desayunos_en_orden"),
    ]

    operations = [
        migrations.RunPython(apply_product_update, restore_previous_product),
    ]
