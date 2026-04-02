from django.contrib import admin
from .models import Categoria, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'destacado')
    list_filter = ('categoria', 'destacado')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'destacado')