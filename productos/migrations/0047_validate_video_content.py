import django.core.validators
import productos.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("productos", "0046_renombrar_referencias_sin_premium")]

    operations = [
        migrations.AlterField(
            model_name="videoelaboracion",
            name="video",
            field=models.FileField(
                help_text="Formatos permitidos: MP4, WEBM o MOV. Tamaño máximo: 30 MB.",
                upload_to="procesos/videos/",
                validators=[
                    django.core.validators.FileExtensionValidator(["mp4", "webm", "mov"]),
                    productos.models.validate_video_size,
                    productos.models.validate_video_content,
                ],
            ),
        ),
    ]
