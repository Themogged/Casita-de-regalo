from django.contrib import admin

from .models import Carrito, CarritoItem


class CarritoItemInline(admin.TabularInline):
    model = CarritoItem
    extra = 0
    readonly_fields = ("producto", "cantidad", "actualizado")


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "session_key", "actualizado")
    search_fields = ("usuario__username", "session_key", "items__producto__nombre")
    readonly_fields = ("creado", "actualizado")
    inlines = (CarritoItemInline,)
