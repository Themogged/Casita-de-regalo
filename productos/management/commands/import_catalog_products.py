import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from productos.models import Categoria, Producto


REQUIRED_FIELDS = {'nombre', 'categoria', 'precio'}


class Command(BaseCommand):
    help = 'Importa o actualiza productos desde un archivo JSON controlado.'

    def add_arguments(self, parser):
        parser.add_argument('json_path', help='Ruta del archivo JSON con una lista de productos.')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Valida y muestra el resultado sin escribir en la base de datos.',
        )
        parser.add_argument(
            '--no-update',
            action='store_true',
            help='No actualiza productos existentes; solo crea los nuevos.',
        )

    def handle(self, *args, **options):
        json_path = Path(options['json_path']).resolve()
        if not json_path.exists():
            raise CommandError(f'No existe el archivo: {json_path}')

        try:
            payload = json.loads(json_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise CommandError(f'JSON inválido: {exc}') from exc

        if not isinstance(payload, list):
            raise CommandError('El archivo debe contener una lista de productos.')

        products = [self._normalize_item(item, index) for index, item in enumerate(payload, start=1)]
        dry_run = options['dry_run']
        update_existing = not options['no_update']

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for item in products:
                categoria, _ = Categoria.objects.get_or_create(nombre=item['categoria'])
                defaults = {
                    'descripcion': item['descripcion'],
                    'precio': item['precio'],
                    'stock': item['stock'],
                    'categoria': categoria,
                    'imagen': item['imagen'],
                    'destacado': item['destacado'],
                }

                existing = Producto.objects.filter(nombre=item['nombre']).first()
                if existing and not update_existing:
                    skipped += 1
                    continue

                if existing:
                    for field, value in defaults.items():
                        setattr(existing, field, value)
                    existing.save(update_fields=[*defaults.keys()])
                    updated += 1
                else:
                    Producto.objects.create(nombre=item['nombre'], **defaults)
                    created += 1

            if dry_run:
                transaction.set_rollback(True)

        mode = 'DRY RUN - ' if dry_run else ''
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode}productos revisados: {len(products)}. Creados: {created}. '
                f'Actualizados: {updated}. Omitidos: {skipped}.'
            )
        )

    def _normalize_item(self, item, index):
        if not isinstance(item, dict):
            raise CommandError(f'El producto #{index} debe ser un objeto JSON.')

        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise CommandError(f'El producto #{index} no tiene campos requeridos: {", ".join(sorted(missing))}.')

        try:
            precio = Decimal(str(item['precio']))
        except (InvalidOperation, TypeError) as exc:
            raise CommandError(f'El producto #{index} tiene precio inválido.') from exc

        if precio < 0:
            raise CommandError(f'El producto #{index} tiene precio negativo.')

        try:
            stock = int(item.get('stock', 100))
        except (TypeError, ValueError) as exc:
            raise CommandError(f'El producto #{index} tiene stock inválido.') from exc

        return {
            'nombre': str(item['nombre']).strip(),
            'categoria': str(item['categoria']).strip(),
            'descripcion': str(item.get('descripcion', '')).strip(),
            'precio': precio,
            'stock': max(0, stock),
            'imagen': str(item.get('imagen', '')).strip(),
            'destacado': bool(item.get('destacado', False)),
        }
