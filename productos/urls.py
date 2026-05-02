from django.urls import path

from .assistant_views import assistant_chat
from .views import aviso_privacidad, detalle_producto, inicio, terminos_condiciones

urlpatterns = [
    path('', inicio, name='inicio'),
    path('producto/<int:producto_id>/', detalle_producto, name='detalle_producto'),
    path('terminos-y-condiciones/', terminos_condiciones, name='terminos_condiciones'),
    path('aviso-de-privacidad/', aviso_privacidad, name='aviso_privacidad'),
    path('asistente/chat/', assistant_chat, name='assistant_chat'),
]
