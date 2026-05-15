from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Categoria, InteraccionCliente, Producto, ProductoImagen, VideoElaboracion


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


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'total_productos')
    search_fields = ('nombre',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total_productos_count=Count('producto'))

    @admin.display(description='Productos', ordering='total_productos_count')
    def total_productos(self, obj):
        return obj.total_productos_count


class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1
    fields = ('preview', 'imagen', 'titulo', 'orden')
    readonly_fields = ('preview',)

    @admin.display(description='Vista previa')
    def preview(self, obj):
        if not obj.pk or not obj.imagen:
            return 'Sin imagen'
        return format_html(
            '<img src="{}" style="width:76px;height:76px;object-fit:cover;border-radius:12px;" alt="">',
            obj.imagen.url,
        )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('preview', 'nombre', 'precio', 'stock', 'estado_publico', 'categoria', 'destacado', 'fecha_creacion')
    list_filter = ('categoria', 'destacado', DisponibilidadFilter, 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'destacado')
    list_select_related = ('categoria',)
    readonly_fields = ('preview_grande', 'fecha_creacion')
    date_hierarchy = 'fecha_creacion'
    ordering = ('-destacado', 'categoria__nombre', 'nombre')
    inlines = (ProductoImagenInline,)
    actions = ('marcar_destacado', 'quitar_destacado', 'restablecer_stock_100', 'marcar_agotado')
    fieldsets = (
        (
            'Información principal',
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

    @admin.display(description='Imagen')
    def preview(self, obj):
        if not obj.imagen:
            return format_html('<span style="color:#999;">Sin imagen</span>')
        return format_html(
            '<img src="{}" style="width:58px;height:58px;object-fit:cover;border-radius:14px;border:1px solid #f0d7e2;" alt="">',
            obj.imagen.url,
        )

    @admin.display(description='Vista previa')
    def preview_grande(self, obj):
        if not obj.pk or not obj.imagen:
            return 'Sin imagen cargada'
        return format_html(
            '<img src="{}" style="max-width:220px;max-height:260px;object-fit:contain;border-radius:18px;border:1px solid #f0d7e2;background:#fff7fb;padding:8px;" alt="">',
            obj.imagen.url,
        )

    @admin.display(description='Estado', ordering='stock')
    def estado_publico(self, obj):
        if obj.stock <= 0:
            color = '#b91c1c'
            label = 'Agotado'
        elif obj.stock <= 3:
            color = '#b45309'
            label = 'Stock bajo'
        else:
            color = '#047857'
            label = 'Disponible'
        return format_html('<strong style="color:{};">{}</strong>', color, label)

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


@admin.register(InteraccionCliente)
class InteraccionClienteAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'etiqueta', 'pagina', 'destino_corto', 'creado')
    list_filter = ('tipo', 'creado')
    search_fields = ('etiqueta', 'destino', 'pagina', 'user_agent')
    readonly_fields = ('tipo', 'etiqueta', 'destino', 'pagina', 'user_agent', 'creado')
    date_hierarchy = 'creado'

    @admin.display(description='Destino')
    def destino_corto(self, obj):
        if not obj.destino:
            return '-'
        return obj.destino[:70] + ('...' if len(obj.destino) > 70 else '')


@admin.register(VideoElaboracion)
class VideoElaboracionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'preview_portada', 'activo', 'destacado', 'orden', 'fecha_creacion')
    list_filter = ('activo', 'destacado', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion')
    list_editable = ('activo', 'destacado', 'orden')
    readonly_fields = ('preview_portada', 'fecha_creacion')
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
            return '-'
        return format_html(
            '<img src="{}" style="width:76px;height:76px;object-fit:cover;border-radius:12px;" alt="">',
            obj.portada.url,
        )
