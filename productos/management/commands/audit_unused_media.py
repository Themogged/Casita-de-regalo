from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from productos.models import Producto, ProductoImagen, VideoElaboracion


class Command(BaseCommand):
    help = 'Audita archivos dentro de media que no están referenciados por el catálogo.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=str(settings.MEDIA_ROOT),
            help='Ruta absoluta o relativa a BASE_DIR que se quiere auditar.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=80,
            help='Cantidad máxima de archivos huérfanos a listar.',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['path'])
        if not source_dir.is_absolute():
            source_dir = Path(settings.BASE_DIR) / source_dir

        source_dir = source_dir.resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()

        if not source_dir.exists():
            raise CommandError(f'La ruta no existe: {source_dir}')

        try:
            source_dir.relative_to(media_root)
        except ValueError as exc:
            raise CommandError('Por seguridad, la auditoría solo puede ejecutarse dentro de MEDIA_ROOT.') from exc

        referenced = self._referenced_media_paths(media_root)
        scanned_files = [
            path
            for path in source_dir.rglob('*')
            if path.is_file() and not path.name.startswith('.')
        ]
        orphan_files = [path for path in scanned_files if path.resolve() not in referenced]

        self.stdout.write(f'Archivos revisados: {len(scanned_files)}')
        self.stdout.write(f'Archivos referenciados conocidos: {len(referenced)}')
        self.stdout.write(f'Posibles huérfanos: {len(orphan_files)}')

        for path in orphan_files[: max(0, options['limit'])]:
            self.stdout.write(f'- {path.relative_to(media_root).as_posix()}')

        if len(orphan_files) > options['limit']:
            self.stdout.write(f'... {len(orphan_files) - options["limit"]} más no listados.')

        self.stdout.write(
            self.style.WARNING(
                'Este comando no borra archivos. Revisa manualmente antes de eliminar media.'
            )
        )

    def _referenced_media_paths(self, media_root):
        values = []
        values.extend(Producto.objects.exclude(imagen='').values_list('imagen', flat=True))
        values.extend(ProductoImagen.objects.exclude(imagen='').values_list('imagen', flat=True))
        values.extend(VideoElaboracion.objects.exclude(video='').values_list('video', flat=True))
        values.extend(VideoElaboracion.objects.exclude(portada='').values_list('portada', flat=True))

        referenced = set()
        for value in values:
            if not value:
                continue
            referenced.add((media_root / value).resolve())
            if Path(value).suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                referenced.add((media_root / value).with_suffix('.webp').resolve())
        return referenced
