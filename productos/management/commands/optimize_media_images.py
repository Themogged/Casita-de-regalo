from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps, UnidentifiedImageError


SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}


class Command(BaseCommand):
    help = 'Genera versiones WebP optimizadas para imagenes JPG, JPEG y PNG dentro de media.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=str(settings.MEDIA_ROOT),
            help='Ruta absoluta o relativa a BASE_DIR que se quiere optimizar.',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=78,
            help='Calidad WebP de salida. Recomendado: 70 a 82.',
        )
        parser.add_argument(
            '--max-width',
            type=int,
            default=1400,
            help='Ancho maximo en pixeles. Mantiene proporcion.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenera archivos WebP aunque ya existan.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra cuantas imagenes se optimizarian sin escribir archivos.',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['path'])
        if not source_dir.is_absolute():
            source_dir = Path(settings.BASE_DIR) / source_dir

        source_dir = source_dir.resolve()
        if not source_dir.exists():
            raise CommandError(f'La ruta no existe: {source_dir}')

        quality = max(1, min(100, options['quality']))
        max_width = max(320, options['max_width'])
        force = options['force']
        dry_run = options['dry_run']

        total = 0
        created = 0
        skipped = 0
        failed = 0

        for image_path in sorted(source_dir.rglob('*')):
            if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            total += 1
            webp_path = image_path.with_suffix('.webp')

            if webp_path.exists() and not force:
                skipped += 1
                continue

            try:
                with Image.open(image_path) as image:
                    optimized = ImageOps.exif_transpose(image)
                    optimized.thumbnail((max_width, max_width * 2), Image.Resampling.LANCZOS)

                    if optimized.mode not in {'RGB', 'RGBA'}:
                        optimized = optimized.convert('RGBA' if 'A' in optimized.getbands() else 'RGB')

                    if not dry_run:
                        webp_path.parent.mkdir(parents=True, exist_ok=True)
                        optimized.save(webp_path, 'WEBP', quality=quality, method=6)
                    created += 1
            except (OSError, UnidentifiedImageError) as exc:
                failed += 1
                self.stderr.write(f'No se pudo optimizar {image_path}: {exc}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Imagenes revisadas: {total}. WebP {"por crear" if dry_run else "creadas"}: {created}. '
                f'Omitidas: {skipped}. Errores: {failed}.'
            )
        )
