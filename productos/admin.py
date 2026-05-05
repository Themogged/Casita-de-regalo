from django.contrib import admin

from .models import Categoria, InteraccionCliente, Producto, ProductoImagen

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)


class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1
    fields = ('imagen', 'titulo', 'orden')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'destacado')
    list_filter = ('categoria', 'destacado')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'destacado')
    inlines = (ProductoImagenInline,)


@admin.register(InteraccionCliente)
class InteraccionClienteAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'etiqueta', 'pagina', 'creado')
    list_filter = ('tipo', 'creado')
    search_fields = ('etiqueta', 'destino', 'pagina', 'user_agent')
    readonly_fields = ('tipo', 'etiqueta', 'destino', 'pagina', 'user_agent', 'creado')
