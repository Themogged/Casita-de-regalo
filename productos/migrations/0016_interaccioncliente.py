from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0015_set_product_stock_to_100'),
    ]

    operations = [
        migrations.CreateModel(
            name='InteraccionCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('whatsapp', 'WhatsApp'), ('instagram', 'Instagram'), ('carrito', 'Carrito'), ('catalogo', 'Catalogo'), ('otro', 'Otro')], default='otro', max_length=40)),
                ('etiqueta', models.CharField(blank=True, max_length=120)),
                ('destino', models.URLField(blank=True, max_length=500)),
                ('pagina', models.CharField(blank=True, max_length=300)),
                ('user_agent', models.CharField(blank=True, max_length=300)),
                ('creado', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'interaccion de cliente',
                'verbose_name_plural': 'interacciones de clientes',
                'ordering': ['-creado'],
            },
        ),
    ]
