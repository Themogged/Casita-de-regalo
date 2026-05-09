from django.db import migrations


VIDEOS_ELABORACION = [
    {
        'titulo': 'Detalle romántico con peluche y rosas',
        'descripcion': (
            'Proceso de armado para un regalo romántico con flores, peluche y composición delicada.'
        ),
        'video': 'procesos/videos/elaboracion-casita-01.mp4',
        'orden': 1,
        'destacado': True,
    },
    {
        'titulo': 'Armado de caja personalizada',
        'descripcion': (
            'Preparación de la base, papelería decorativa y distribución interna antes de completar el detalle.'
        ),
        'video': 'procesos/videos/elaboracion-casita-02.mp4',
        'orden': 2,
        'destacado': True,
    },
    {
        'titulo': 'Ancheta floral lista para entregar',
        'descripcion': (
            'Vista del montaje con flores, bebidas y complementos organizados para una presentación especial.'
        ),
        'video': 'procesos/videos/elaboracion-casita-03.mp4',
        'orden': 3,
        'destacado': False,
    },
    {
        'titulo': 'Detalle temático personalizado',
        'descripcion': (
            'Preparación de un diseño colorido con decoración temática, acabado visual y toque personalizado.'
        ),
        'video': 'procesos/videos/elaboracion-casita-04.mp4',
        'orden': 4,
        'destacado': False,
    },
]


def seed_videos_elaboracion(apps, schema_editor):
    VideoElaboracion = apps.get_model('productos', 'VideoElaboracion')
    for item in VIDEOS_ELABORACION:
        VideoElaboracion.objects.update_or_create(
            video=item['video'],
            defaults={
                'titulo': item['titulo'],
                'descripcion': item['descripcion'],
                'activo': True,
                'destacado': item['destacado'],
                'orden': item['orden'],
            },
        )


def remove_videos_elaboracion(apps, schema_editor):
    VideoElaboracion = apps.get_model('productos', 'VideoElaboracion')
    VideoElaboracion.objects.filter(
        video__in=[item['video'] for item in VIDEOS_ELABORACION]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0017_videoelaboracion'),
    ]

    operations = [
        migrations.RunPython(seed_videos_elaboracion, remove_videos_elaboracion),
    ]
