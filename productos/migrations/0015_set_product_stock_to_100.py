from django.db import migrations


def set_product_stock_to_100(apps, schema_editor):
    Producto = apps.get_model('productos', 'Producto')
    Producto.objects.all().update(stock=100)


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0014_renombrar_guerreras_kpop'),
    ]

    operations = [
        migrations.RunPython(set_product_stock_to_100, migrations.RunPython.noop),
    ]
