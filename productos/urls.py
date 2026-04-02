from django.urls import path

from .views import detalle_producto, inicio

urlpatterns = [
    path('', inicio, name='inicio'),
    path('producto/<int:producto_id>/', detalle_producto, name='detalle_producto'),
]
