import sqlite3
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from productos.image_frames import ProductFrameError, generate_yellow_child_frame, slugify_filename
from productos.models import Producto


class Command(BaseCommand):
    help = "Genera marcos amarillos para productos de la categoría Temáticos e infantiles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--category",
            default="Temáticos e infantiles",
            help="Nombre exacto de la categoría que se va a procesar.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los productos que se procesarian sin escribir imagenes ni actualizar la base de datos.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenera imagenes aunque el archivo de salida ya exista.",
        )
        parser.add_argument(
            "--source-db",
            default="",
            help="SQLite de respaldo desde donde tomar las rutas originales de imagen por producto.",
        )
        parser.add_argument(
            "--quality",
            type=int,
            default=88,
            help="Calidad WebP de salida entre 1 y 100.",
        )

    def handle(self, *args, **options):
        category_name = options["category"]
        dry_run = options["dry_run"]
        force = options["force"]
        quality = max(1, min(100, options["quality"]))
        source_images = self._load_source_images(options["source_db"]) if options["source_db"] else {}

        products = list(
            Producto.objects.select_related("categoria")
            .filter(categoria__nombre=category_name)
            .order_by("id")
        )
        if not products:
            raise CommandError(f"No se encontraron productos en la categoría: {category_name}")

        logo_path = Path(settings.MEDIA_ROOT) / "branding" / "logo-casita.webp"
        output_dir = Path(settings.MEDIA_ROOT) / "productos" / "tematicos" / "enmarcados"

        if not logo_path.exists():
            raise CommandError(f"No existe el logo esperado: {logo_path}")

        self.stdout.write(f"Categoria: {category_name}")
        self.stdout.write(f"Productos encontrados: {len(products)}")
        self.stdout.write(f"Destino: {output_dir}")

        if dry_run:
            for product in products:
                status = "OK" if product.imagen else "SIN_IMAGEN"
                output_name = self._build_output_name(product)
                source_name = source_images.get(product.id, product.imagen.name if product.imagen else "")
                self.stdout.write(f"[dry-run] {product.id} - {product.nombre} - {status} - origen: {source_name} -> {output_name}")
            return

        backup_path = self._backup_database()
        self.stdout.write(f"Backup de base de datos: {backup_path}")

        created = 0
        updated = 0
        skipped = 0
        failed = 0

        with transaction.atomic():
            for product in products:
                if not product.imagen:
                    skipped += 1
                    self.stderr.write(f"Omitido sin imagen: {product.id} - {product.nombre}")
                    continue

                source_name = source_images.get(product.id)
                source_path = Path(settings.MEDIA_ROOT) / source_name if source_name else Path(product.imagen.path)
                output_path = output_dir / self._build_output_name(product)
                relative_output = output_path.relative_to(Path(settings.MEDIA_ROOT)).as_posix()

                if self._is_inside(source_path, output_dir):
                    skipped += 1
                    self.stdout.write(f"Ya apunta a imagen enmarcada: {product.nombre} -> {product.imagen.name}")
                    continue

                if output_path.exists() and not force:
                    skipped += 1
                    if product.imagen.name != relative_output:
                        product.imagen.name = relative_output
                        product.save(update_fields=["imagen"])
                        updated += 1
                    self.stdout.write(f"Ya existia: {product.nombre} -> {relative_output}")
                    continue

                try:
                    generate_yellow_child_frame(
                        source_path,
                        logo_path,
                        output_path,
                        product.nombre,
                        quality=quality,
                    )
                except ProductFrameError as exc:
                    failed += 1
                    self.stderr.write(str(exc))
                    continue

                created += 1
                product.imagen.name = relative_output
                product.save(update_fields=["imagen"])
                updated += 1
                self.stdout.write(f"Enmarcado: {product.nombre} -> {relative_output}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo. Creadas: {created}. Actualizadas: {updated}. Omitidas: {skipped}. Errores: {failed}."
            )
        )

    def _build_output_name(self, product):
        return f"{product.id:03d}-{slugify_filename(product.nombre)}-marco-amarillo.webp"

    def _backup_database(self):
        db_settings = settings.DATABASES["default"]
        db_path = Path(db_settings.get("NAME", ""))
        if db_settings.get("ENGINE") != "django.db.backends.sqlite3" or not db_path.exists():
            return "omitido: la base de datos default no es SQLite local"

        timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
        backup_path = db_path.with_name(f"{db_path.stem}-backup-marcos-infantiles-{timestamp}{db_path.suffix}")
        shutil.copy2(db_path, backup_path)
        return backup_path

    def _load_source_images(self, source_db):
        source_db_path = Path(source_db)
        if not source_db_path.is_absolute():
            source_db_path = Path(settings.BASE_DIR) / source_db_path
        if not source_db_path.exists():
            raise CommandError(f"No existe la base de respaldo indicada: {source_db_path}")

        with sqlite3.connect(source_db_path) as connection:
            rows = connection.execute("SELECT id, imagen FROM productos_producto WHERE imagen IS NOT NULL").fetchall()
        return {product_id: image_name for product_id, image_name in rows if image_name}

    def _is_inside(self, path, directory):
        try:
            path.resolve().relative_to(directory.resolve())
        except ValueError:
            return False
        return True
