from django.urls import path
from .views import (
    agregar_al_carrito,
    ver_carrito,
    sumar_producto,
    restar_producto,
    eliminar_producto,
    enviar_carrito_whatsapp,
    resumen_carrito,
    sumar_item,
    restar_item,
    eliminar_item,
    editar_item_personalizacion,
)

urlpatterns = [
    path('', ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_carrito'),
    path('item/<int:item_id>/sumar/', sumar_item, name='sumar_item'),
    path('item/<int:item_id>/restar/', restar_item, name='restar_item'),
    path('item/<int:item_id>/eliminar/', eliminar_item, name='eliminar_item'),
    path(
        'item/<int:item_id>/personalizacion/',
        editar_item_personalizacion,
        name='editar_item_personalizacion',
    ),
    # Rutas heredadas para enlaces o sesiones anteriores a las líneas configurables.
    path('sumar/<int:producto_id>/', sumar_producto, name='sumar_producto'),
    path('restar/<int:producto_id>/', restar_producto, name='restar_producto'),
    path('eliminar/<int:producto_id>/', eliminar_producto, name='eliminar_producto'),
    path('comprar/', enviar_carrito_whatsapp, name='comprar_whatsapp'),
    path('resumen/', resumen_carrito, name='resumen_carrito'),
]
