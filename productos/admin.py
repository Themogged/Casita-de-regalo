from django.contrib import admin
from .models import Categoria, Producto, ProductoImagen

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
