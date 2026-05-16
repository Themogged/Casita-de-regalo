from django.db import migrations


PRODUCT_TEXTS = {
    "Cumple azul premium": {
        "descripcion": (
            "Referencia cumpleañera con caja en madera, globos, fruta, waffles y decoración. "
            "Precio base sujeto a personalización."
        ),
    },
    "Desayuno globos pastel": {
        "descripcion": "Bandeja sorpresa con globos, yogurt, sándwich, jugo y detalles visuales suaves.",
    },
    "Caja aniversario te amo": {
        "descripcion": "Caja romántica con globo burbuja, waffles, jugo y mensaje especial.",
    },
    "Amor delicado rosa": {
        "descripcion": "Referencia romántica en tonos rosa con globo, dulces y presentación suave.",
    },
    "Cumple lila fantasia": {
        "nombre": "Cumple lila fantasía",
        "descripcion": "Opción juvenil y colorida con snacks, desayuno y decoración personalizada.",
    },
    "Black and gold deluxe": {
        "descripcion": "Detalle premium con globos negro y dorado, fruta y una presentación más sofisticada.",
    },
    "Trio corazones sorpresa": {
        "nombre": "Trío corazones sorpresa",
        "descripcion": "Colección romántica con corazones, chocolates, rosas y cajas para sorprender.",
    },
    "Bunny y corazon frutal": {
        "nombre": "Bunny y corazón frutal",
        "descripcion": "Detalle creativo con temática tierna y tabla frutal en forma de corazón.",
    },
    "Buenos dias con amor": {
        "nombre": "Buenos días con amor",
        "descripcion": "Desayuno pequeño con bebidas, snacks y mensaje para sorprender desde temprano.",
    },
    "Dia especial express": {
        "nombre": "Día especial express",
        "descripcion": "Mini detalle con empaque protagonista para regalos rápidos y fechas cortas.",
    },
    "Desayuno mariposa rosa": {
        "descripcion": "Mesa o bandeja en madera con globos, yogurt, jugo y decoración femenina.",
    },
    "Combo snack con globos": {
        "descripcion": "Combinación de snacks y globos metalizados para una sorpresa vistosa.",
    },
    "Caja corazón premium": {
        "descripcion": "Caja fina en forma de corazón con sándwich, jugo, rosas, chocolates o peluche.",
    },
    "Caja corazon premium": {
        "nombre": "Caja corazón premium",
        "descripcion": "Caja fina en forma de corazón con sándwich, jugo, rosas, chocolates o peluche.",
    },
    "Referencia para hombres premium": {
        "descripcion": (
            "Detalle de referencia para cotizar opciones sobrias, snacks, globos y acabados elegantes "
            "para cumpleaños, aniversario o sorpresa especial."
        ),
    },
}


REVERSE_TEXTS = {
    "Cumple azul premium": {
        "descripcion": (
            "Referencia cumpleanera con caja en madera, globos, fruta, waffles y decoracion. "
            "Precio base sujeto a personalizacion."
        ),
    },
    "Desayuno globos pastel": {
        "descripcion": "Bandeja sorpresa con globos, yogurt, sandwich, jugo y detalles visuales suaves.",
    },
    "Caja aniversario te amo": {
        "descripcion": "Caja romantica con globo burbuja, waffles, jugo y mensaje especial.",
    },
    "Amor delicado rosa": {
        "descripcion": "Referencia romantica en tonos rosa con globo, dulces y presentacion suave.",
    },
    "Cumple lila fantasía": {
        "nombre": "Cumple lila fantasia",
        "descripcion": "Opcion juvenil y colorida con snacks, desayuno y decoracion personalizada.",
    },
    "Black and gold deluxe": {
        "descripcion": "Detalle premium con globos negro y dorado, fruta y una presentacion mas sofisticada.",
    },
    "Trío corazones sorpresa": {
        "nombre": "Trio corazones sorpresa",
        "descripcion": "Coleccion romantica con corazones, chocolates, rosas y cajas para sorprender.",
    },
    "Bunny y corazón frutal": {
        "nombre": "Bunny y corazon frutal",
        "descripcion": "Detalle creativo con tematica tierna y tabla frutal en forma de corazon.",
    },
    "Buenos días con amor": {
        "nombre": "Buenos dias con amor",
        "descripcion": "Desayuno pequeno con bebidas, snacks y mensaje para sorprender desde temprano.",
    },
    "Día especial express": {
        "nombre": "Dia especial express",
        "descripcion": "Mini detalle con empaque protagonista para regalos rapidos y fechas cortas.",
    },
    "Desayuno mariposa rosa": {
        "descripcion": "Mesa o bandeja en madera con globos, yogurt, jugo y decoracion femenina.",
    },
    "Combo snack con globos": {
        "descripcion": "Combinacion de snacks y globos metalizados para una sorpresa vistosa.",
    },
    "Caja corazón premium": {
        "nombre": "Caja corazon premium",
        "descripcion": "Caja fina en forma de corazon con sandwich, jugo, rosas, chocolates o peluche.",
    },
    "Referencia para hombres premium": {
        "descripcion": (
            "Detalle de referencia para cotizar opciones sobrias, snacks, globos y acabados elegantes "
            "para cumpleaños, aniversario o sorpresa especial."
        ),
    },
}


def apply_texts(apps, text_map):
    Producto = apps.get_model("productos", "Producto")
    for current_name, values in text_map.items():
        product = Producto.objects.filter(nombre=current_name).first()
        if not product:
            continue

        for field, value in values.items():
            setattr(product, field, value)
        product.save(update_fields=list(values.keys()))


def forwards(apps, schema_editor):
    apply_texts(apps, PRODUCT_TEXTS)


def backwards(apps, schema_editor):
    apply_texts(apps, REVERSE_TEXTS)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0030_actualizar_desayuno_cajita_mama"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
