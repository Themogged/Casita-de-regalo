from django.contrib import admin

from .models import Carrito, CarritoItem


class CarritoItemInline(admin.TabularInline):
    model = CarritoItem
    extra = 0
    readonly_fields = ("producto", "cantidad", "actualizado")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "session_key", "actualizado")
    search_fields = ("usuario__username", "session_key", "items__producto__nombre")
    readonly_fields = ("creado", "actualizado")
    inlines = (CarritoItemInline,)
    list_per_page = 25

    def has_add_permission(self, request):
        # Los carritos se crean desde la tienda; el panel solo los inspecciona.
        return False
