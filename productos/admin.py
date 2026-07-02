import csv

from django.contrib import admin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from .models import Categoria, Producto, ProductoImagen, VideoElaboracion


class DisponibilidadFilter(admin.SimpleListFilter):
    title = 'disponibilidad'
    parameter_name = 'disponibilidad'

    def lookups(self, request, model_admin):
        return (
            ('disponible', 'Disponible'),
            ('agotado', 'Agotado'),
            ('bajo', 'Stock bajo'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'disponible':
            return queryset.filter(stock__gt=0)
        if self.value() == 'agotado':
            return queryset.filter(stock=0)
        if self.value() == 'bajo':
            return queryset.filter(stock__gt=0, stock__lte=3)
        return queryset


class ImagenProductoFilter(admin.SimpleListFilter):
    title = 'imagen'
    parameter_name = 'imagen_estado'

    def lookups(self, request, model_admin):
        return (
            ('con_imagen', 'Con imagen'),
            ('sin_imagen', 'Sin imagen'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'con_imagen':
            return queryset.exclude(Q(imagen='') | Q(imagen__isnull=True))
        if self.value() == 'sin_imagen':
            return queryset.filter(Q(imagen='') | Q(imagen__isnull=True))
        return queryset


class GaleriaProductoFilter(admin.SimpleListFilter):
    title = 'galeria'
    parameter_name = 'galeria_estado'

    def lookups(self, request, model_admin):
        return (
            ('con_galeria', 'Con galeria'),
            ('sin_galeria', 'Sin galeria'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'con_galeria':
            return queryset.filter(imagenes__isnull=False).distinct()
        if self.value() == 'sin_galeria':
            return queryset.filter(imagenes__isnull=True)
        return queryset


def _admin_badge(label, status='neutral', title=None):
    if title:
        return format_html(
            '<span class="casita-admin-badge is-{}" title="{}">{}</span>',
            status,
            title,
            label,
        )
    return format_html('<span class="casita-admin-badge is-{}">{}</span>', status, label)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'total_productos', 'productos_disponibles', 'productos_agotados', 'ver_catalogo')
    search_fields = ('nombre',)
    ordering = ('nombre',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            total_productos_count=Count('producto', distinct=True),
            productos_disponibles_count=Count(
                'producto',
                filter=Q(producto__stock__gt=0),
                distinct=True,
            ),
            productos_agotados_count=Count(
                'producto',
                filter=Q(producto__stock=0),
                distinct=True,
            ),
        )

    @admin.display(description='Productos', ordering='total_productos_count')
    def total_productos(self, obj):
        return format_html('<span class="casita-admin-count">{}</span>', obj.total_productos_count)

    @admin.display(description='Disponibles', ordering='productos_disponibles_count')
    def productos_disponibles(self, obj):
        return _admin_badge(obj.productos_disponibles_count, 'success')

    @admin.display(description='Agotados', ordering='productos_agotados_count')
    def productos_agotados(self, obj):
        status = 'danger' if obj.productos_agotados_count else 'neutral'
        return _admin_badge(obj.productos_agotados_count, status)

    @admin.display(description='Tienda')
    def ver_catalogo(self, obj):
        url = f"{reverse('catalogo')}?{urlencode({'categoria': obj.pk})}#catalogo"
        return format_html(
            '<a class="casita-admin-link" href="{}" target="_blank" rel="noopener noreferrer">Ver catalogo</a>',
            url,
        )


class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1
    fields = ('preview', 'imagen', 'titulo', 'orden')
    readonly_fields = ('preview',)

    @admin.display(description='Vista previa')
    def preview(self, obj):
        if not obj.pk or not obj.imagen:
            return format_html('<span class="casita-admin-empty">Sin imagen</span>')
        return format_html(
            '<img src="{}" class="casita-admin-thumb is-large" alt="">',
            obj.imagen.url,
        )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'preview',
        'nombre',
        'categoria',
        'precio',
        'stock',
        'estado_publico',
        'galeria_estado',
        'destacado',
        'ver_en_tienda',
        'fecha_creacion',
    )
    list_filter = (
        'categoria',
        'destacado',
        DisponibilidadFilter,
        ImagenProductoFilter,
        GaleriaProductoFilter,
        'fecha_creacion',
    )
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'destacado')
    list_select_related = ('categoria',)
    readonly_fields = ('preview_grande', 'fecha_creacion')
    date_hierarchy = 'fecha_creacion'
    ordering = ('-destacado', 'categoria__nombre', 'nombre')
    inlines = (ProductoImagenInline,)
    actions = ('marcar_destacado', 'quitar_destacado', 'restablecer_stock_100', 'marcar_agotado', 'exportar_productos_csv')
    autocomplete_fields = ('categoria',)
    list_per_page = 40
    save_on_top = True
    show_full_result_count = False
    fieldsets = (
        (
            'Informacion principal',
            {
                'fields': ('preview_grande', 'nombre', 'descripcion', 'categoria', 'imagen'),
            },
        ),
        (
            'Venta y visibilidad',
            {
                'fields': ('precio', 'stock', 'destacado', 'fecha_creacion'),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            galeria_count=Count('imagenes', distinct=True),
        )

    @admin.display(description='Imagen')
    def preview(self, obj):
        if not obj.imagen:
            return format_html('<span class="casita-admin-empty">Sin imagen</span>')
        return format_html(
            '<img src="{}" class="casita-admin-thumb" alt="">',
            obj.imagen.url,
        )

    @admin.display(description='Vista previa')
    def preview_grande(self, obj):
        if not obj.pk or not obj.imagen:
            return format_html('<span class="casita-admin-empty">Sin imagen cargada</span>')
        return format_html(
            '<img src="{}" class="casita-admin-preview" alt="">',
            obj.imagen.url,
        )

    @admin.display(description='Estado', ordering='stock')
    def estado_publico(self, obj):
        if obj.stock <= 0:
            return _admin_badge('Agotado', 'danger')
        elif obj.stock <= 3:
            return _admin_badge('Stock bajo', 'warning')
        return _admin_badge('Disponible', 'success')

    @admin.display(description='Galeria', ordering='galeria_count')
    def galeria_estado(self, obj):
        total_galeria = getattr(obj, 'galeria_count', None)
        if total_galeria is None:
            total_galeria = obj.imagenes.count()

        if obj.imagen and total_galeria:
            return _admin_badge(f'Principal + {total_galeria}', 'success')
        if obj.imagen:
            return _admin_badge('Principal', 'neutral')
        if total_galeria:
            return _admin_badge(f'{total_galeria} en galeria', 'warning')
        return _admin_badge('Sin imagenes', 'danger')

    @admin.display(description='Tienda')
    def ver_en_tienda(self, obj):
        if not obj.pk:
            return '-'
        return format_html(
            '<a class="casita-admin-link" href="{}" target="_blank" rel="noopener noreferrer">Ver</a>',
            reverse('detalle_producto', args=[obj.pk]),
        )

    @admin.action(description='Marcar como destacados')
    def marcar_destacado(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} productos marcados como destacados.')

    @admin.action(description='Quitar destacado')
    def quitar_destacado(self, request, queryset):
        updated = queryset.update(destacado=False)
        self.message_user(request, f'{updated} productos dejaron de estar destacados.')

    @admin.action(description='Restablecer stock a 100')
    def restablecer_stock_100(self, request, queryset):
        updated = queryset.update(stock=100)
        self.message_user(request, f'{updated} productos quedaron con stock 100.')

    @admin.action(description='Marcar como agotados')
    def marcar_agotado(self, request, queryset):
        updated = queryset.update(stock=0)
        self.message_user(request, f'{updated} productos quedaron como agotados.')

    @admin.action(description='Exportar productos seleccionados a CSV')
    def exportar_productos_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="productos-casita.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                'ID',
                'Nombre',
                'Categoria',
                'Precio',
                'Stock',
                'Estado',
                'Destacado',
                'Imagen principal',
                'Imagenes galeria',
                'Fecha creacion',
            ]
        )

        productos = queryset.select_related('categoria').annotate(
            galeria_count=Count('imagenes', distinct=True),
        ).order_by('categoria__nombre', 'nombre')
        for producto in productos:
            if producto.stock <= 0:
                estado = 'agotado'
            elif producto.stock <= 3:
                estado = 'stock bajo'
            else:
                estado = 'disponible'

            writer.writerow(
                [
                    producto.pk,
                    producto.nombre,
                    producto.categoria.nombre if producto.categoria else '',
                    producto.precio,
                    producto.stock,
                    estado,
                    'si' if producto.destacado else 'no',
                    str(producto.imagen) if producto.imagen else '',
                    producto.galeria_count,
                    producto.fecha_creacion.isoformat() if producto.fecha_creacion else '',
                ]
            )

        return response


@admin.register(VideoElaboracion)
class VideoElaboracionAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'preview_portada',
        'estado_publicacion',
        'activo',
        'destacado',
        'orden',
        'archivo_video',
        'fecha_creacion',
    )
    list_filter = ('activo', 'destacado', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion')
    list_editable = ('activo', 'destacado', 'orden')
    readonly_fields = ('preview_portada', 'fecha_creacion')
    actions = ('activar_videos', 'desactivar_videos', 'marcar_destacados', 'quitar_destacados')
    list_per_page = 30
    save_on_top = True
    fieldsets = (
        (
            'Contenido',
            {
                'fields': ('titulo', 'descripcion', 'video', 'portada'),
            },
        ),
        (
            'Publicacion',
            {
                'fields': ('activo', 'destacado', 'orden', 'fecha_creacion'),
            },
        ),
    )

    @admin.display(description='Portada')
    def preview_portada(self, obj):
        if not obj.portada:
            return format_html('<span class="casita-admin-empty">Sin portada</span>')
        return format_html(
            '<img src="{}" class="casita-admin-thumb is-large" alt="">',
            obj.portada.url,
        )

    @admin.display(description='Estado', ordering='activo')
    def estado_publicacion(self, obj):
        if obj.activo:
            return _admin_badge('Activo', 'success')
        return _admin_badge('Inactivo', 'neutral')

    @admin.display(description='Video')
    def archivo_video(self, obj):
        if not obj.video:
            return _admin_badge('Sin video', 'danger')
        extension = obj.video.name.rsplit('.', 1)[-1].upper() if '.' in obj.video.name else 'Archivo'
        return _admin_badge(extension, 'neutral', title=obj.video.name)

    @admin.action(description='Activar videos seleccionados')
    def activar_videos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} videos quedaron activos.')

    @admin.action(description='Desactivar videos seleccionados')
    def desactivar_videos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} videos quedaron inactivos.')

    @admin.action(description='Marcar videos como destacados')
    def marcar_destacados(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} videos marcados como destacados.')

    @admin.action(description='Quitar destacado a videos')
    def quitar_destacados(self, request, queryset):
        updated = queryset.update(destacado=False)
        self.message_user(request, f'{updated} videos dejaron de estar destacados.')
