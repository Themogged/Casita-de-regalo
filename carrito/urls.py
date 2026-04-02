from django.urls import path
from .views import (
    agregar_al_carrito,
    ver_carrito,
    sumar_producto,
    restar_producto,
    eliminar_producto,
    enviar_carrito_whatsapp,
)

urlpatterns = [
    path('', ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_carrito'),
    path('sumar/<int:producto_id>/', sumar_producto, name='sumar_producto'),
    path('restar/<int:producto_id>/', restar_producto, name='restar_producto'),
    path('eliminar/<int:producto_id>/', eliminar_producto, name='eliminar_producto'),
    path('comprar/', enviar_carrito_whatsapp, name='comprar_whatsapp'),
]