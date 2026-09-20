import csv

from django.contrib import admin, messages
from django.db.models import Count, Q
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from .forms import ProductoAdminForm, VideoElaboracionAdminForm
from .models import Categoria, Producto, ProductoImagen, VideoElaboracion
from .templatetags.media_optimization import optimized_image_url, responsive_image_srcset


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


def _stored_file_exists(field_file):
    if not field_file or not field_file.name:
        return False
    try:
        return field_file.storage.exists(field_file.name)
    except (OSError, ValueError):
        return False


def _admin_image(image, css_class, sizes):
    if not image:
        return format_html('<span class="casita-admin-empty">{}</span>', 'Sin imagen')

    source_url = image.url
    optimized_url = optimized_image_url(source_url)
    srcset = responsive_image_srcset(source_url)
    if srcset:
        return format_html(
            '<img src="{}" srcset="{}" sizes="{}" class="{}" alt="" '
            'loading="lazy" decoding="async">',
            optimized_url,
            srcset,
            sizes,
            css_class,
        )
    return format_html(
        '<img src="{}" class="{}" alt="" loading="lazy" decoding="async">',
        optimized_url,
        css_class,
    )


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
            return format_html('<span class="casita-admin-empty">{}</span>', 'Sin imagen')
        return _admin_image(obj.imagen, 'casita-admin-thumb is-large', '72px')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoAdminForm
    change_list_template = 'admin/productos/producto/change_list.html'
    list_display = (
        'preview',
        'nombre',
        'categoria',
        'precio',
        'stock',
        'estado_publico',
        'destacado',
        'acciones_rapidas',
    )
    list_display_links = ('nombre',)
    list_filter = (
        'categoria',
        DisponibilidadFilter,
        'destacado',
        ImagenProductoFilter,
    )
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'destacado')
    list_select_related = ('categoria',)
    readonly_fields = ('preview_grande', 'fecha_creacion')
    ordering = ('-destacado', 'categoria__nombre', 'nombre')
    inlines = (ProductoImagenInline,)
    actions = ('marcar_destacado', 'quitar_destacado', 'restablecer_stock_100', 'marcar_agotado', 'exportar_productos_csv')
    autocomplete_fields = ('categoria',)
    list_per_page = 20
    save_on_top = True
    show_full_result_count = False
    fieldsets = (
        (
            'Información principal',
            {
                'fields': ('preview_grande', 'nombre', 'descripcion', 'categoria', 'imagen'),
                'description': 'Información visible para el cliente dentro del catálogo.',
            },
        ),
        (
            'Venta y visibilidad',
            {
                'fields': ('precio', 'stock', 'destacado'),
                'description': 'Controla el precio base, la disponibilidad y la prioridad en la tienda.',
            },
        ),
        (
            'Control del registro',
            {
                'fields': ('fecha_creacion',),
                'classes': ('collapse',),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        stats = self.get_queryset(request).aggregate(
            total=Count('id'),
            available=Count('id', filter=Q(stock__gt=3)),
            low_stock=Count('id', filter=Q(stock__gt=0, stock__lte=3)),
            out_of_stock=Count('id', filter=Q(stock=0)),
            without_image=Count('id', filter=Q(imagen='') | Q(imagen__isnull=True)),
        )
        context = {
            'title': 'Catálogo de productos',
            'catalog_stats': stats,
        }
        if extra_context:
            context.update(extra_context)
        return super().changelist_view(request, extra_context=context)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            galeria_count=Count('imagenes', distinct=True),
        )

    @admin.display(description='Imagen')
    def preview(self, obj):
        return _admin_image(obj.imagen, 'casita-admin-thumb', '64px')

    @admin.display(description='Vista previa')
    def preview_grande(self, obj):
        if not obj.pk or not obj.imagen:
            return format_html('<span class="casita-admin-empty">{}</span>', 'Sin imagen cargada')
        return _admin_image(obj.imagen, 'casita-admin-preview', '(max-width: 767px) 220px, 320px')

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

    @admin.display(description='Acciones')
    def acciones_rapidas(self, obj):
        if not obj.pk:
            return '-'
        return format_html(
            '<span class="casita-admin-row-actions">'
            '<a class="casita-admin-link" href="{}">Editar</a>'
            '<a class="casita-admin-link is-secondary" href="{}" target="_blank" rel="noopener noreferrer">Ver tienda</a>'
            '</span>',
            reverse('admin:productos_producto_change', args=[obj.pk]),
            reverse('detalle_producto', args=[obj.pk]),
        )

    @admin.display(description='Tienda')
    def ver_en_tienda(self, obj):
        """Conserva el enlace publico usado por integraciones y pruebas anteriores."""
        if not obj.pk:
            return '-'
        return format_html(
            '<a class="casita-admin-link is-secondary" href="{}" target="_blank" '
            'rel="noopener noreferrer">Ver tienda</a>',
            reverse('detalle_producto', args=[obj.pk]),
        )

    @admin.action(description='Marcar como destacados')
    def marcar_destacado(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} productos marcados como destacados.', messages.SUCCESS)

    @admin.action(description='Quitar destacado')
    def quitar_destacado(self, request, queryset):
        updated = queryset.update(destacado=False)
        self.message_user(request, f'{updated} productos dejaron de estar destacados.', messages.SUCCESS)

    @admin.action(description='Reponer stock a 100 unidades')
    def restablecer_stock_100(self, request, queryset):
        updated = queryset.update(stock=100)
        self.message_user(request, f'{updated} productos quedaron con stock 100.', messages.SUCCESS)

    @admin.action(description='Marcar como agotados')
    def marcar_agotado(self, request, queryset):
        updated = queryset.update(stock=0)
        self.message_user(request, f'{updated} productos quedaron como agotados.', messages.WARNING)

    @admin.action(description='Exportar productos seleccionados a CSV')
    def exportar_productos_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="productos-casita.csv"'
        response.write('\ufeff')

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
    form = VideoElaboracionAdminForm
    change_list_template = 'admin/productos/videoelaboracion/change_list.html'
    list_display = (
        'preview_portada',
        'titulo',
        'estado_publicacion',
        'activo',
        'destacado',
        'orden',
        'archivo_video',
        'ver_seccion',
    )
    list_display_links = ('titulo',)
    list_filter = ('activo', 'destacado', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion')
    list_editable = ('activo', 'destacado', 'orden')
    readonly_fields = ('preview_video', 'preview_portada', 'fecha_creacion')
    actions = ('activar_videos', 'desactivar_videos', 'marcar_destacados', 'quitar_destacados')
    list_per_page = 20
    save_on_top = True
    fieldsets = (
        (
            'Contenido',
            {
                'fields': ('preview_video', 'titulo', 'descripcion', 'video', 'portada', 'preview_portada'),
                'description': 'Sube el video y revisa aquí mismo cómo se reproducirá antes de publicarlo.',
            },
        ),
        (
            'Publicación',
            {
                'fields': ('activo', 'destacado', 'orden', 'fecha_creacion'),
                'description': 'Activa el contenido cuando esté listo. El orden menor aparece primero.',
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        stats = queryset.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(activo=True)),
            inactive=Count('id', filter=Q(activo=False)),
            featured=Count('id', filter=Q(destacado=True)),
        )
        stats['missing_files'] = sum(
            1 for video in queryset.only('video') if not _stored_file_exists(video.video)
        )
        context = {
            'title': 'Videos de elaboración',
            'video_stats': stats,
        }
        if extra_context:
            context.update(extra_context)
        return super().changelist_view(request, extra_context=context)

    @admin.display(description='Portada')
    def preview_portada(self, obj):
        poster_url = obj.display_poster_url if obj.pk else ''
        if not poster_url:
            return format_html('<span class="casita-admin-empty">{}</span>', 'Sin portada')
        return format_html(
            '<img src="{}" class="casita-admin-thumb is-large" alt="" loading="lazy" decoding="async">',
            poster_url,
        )

    @admin.display(description='Vista previa del video')
    def preview_video(self, obj):
        if not obj.pk or not _stored_file_exists(obj.video):
            return format_html(
                '<div class="casita-admin-file-warning"><strong>Video no disponible</strong>'
                '<span>{}</span></div>',
                'Sube un archivo válido para habilitar la vista previa.',
            )
        poster = obj.display_poster_url
        poster_attribute = format_html(' poster="{}"', poster) if poster else ''
        return format_html(
            '<video class="casita-admin-video-preview" controls preload="metadata"{}>'
            '<source src="{}" type="{}">'
            'Tu navegador no puede reproducir este video.'
            '</video>',
            poster_attribute,
            obj.video.url,
            obj.mime_type,
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
        if not _stored_file_exists(obj.video):
            return _admin_badge(f'{extension} faltante', 'danger', title=obj.video.name)
        return _admin_badge(f'{extension} listo', 'success', title=obj.video.name)

    @admin.display(description='Tienda')
    def ver_seccion(self, obj):
        return format_html(
            '<a class="casita-admin-link is-secondary" href="{}" target="_blank" rel="noopener noreferrer">Ver sección</a>',
            f'{reverse("inicio")}#proceso-real',
        )

    @admin.action(description='Activar videos seleccionados')
    def activar_videos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} videos quedaron activos.', messages.SUCCESS)

    @admin.action(description='Desactivar videos seleccionados')
    def desactivar_videos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} videos quedaron inactivos.', messages.WARNING)

    @admin.action(description='Marcar videos como destacados')
    def marcar_destacados(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} videos marcados como destacados.', messages.SUCCESS)

    @admin.action(description='Quitar destacado a videos')
    def quitar_destacados(self, request, queryset):
        updated = queryset.update(destacado=False)
        self.message_user(request, f'{updated} videos dejaron de estar destacados.', messages.SUCCESS)
