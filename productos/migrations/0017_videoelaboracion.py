import django.core.validators
import productos.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0016_interaccioncliente'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoElaboracion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('descripcion', models.TextField(blank=True)),
                ('video', models.FileField(help_text='Formatos permitidos: MP4, WEBM o MOV. Tamaño máximo: 30 MB.', upload_to='procesos/videos/', validators=[django.core.validators.FileExtensionValidator(['mp4', 'webm', 'mov']), productos.models.validate_video_size])),
                ('portada', models.ImageField(blank=True, null=True, upload_to='procesos/portadas/')),
                ('activo', models.BooleanField(default=True)),
                ('destacado', models.BooleanField(default=False)),
                ('orden', models.PositiveIntegerField(default=0)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'video de elaboracion',
                'verbose_name_plural': 'videos de elaboracion',
                'ordering': ['orden', '-destacado', '-fecha_creacion'],
                'indexes': [models.Index(fields=['activo', 'orden'], name='productos_v_activo_7a190d_idx')],
            },
        ),
    ]
