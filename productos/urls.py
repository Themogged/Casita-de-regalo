from django.urls import path

from .assistant_views import assistant_chat
from .views import aviso_privacidad, como_comprar, detalle_producto, disena_regalo, inicio, preguntas_frecuentes, terminos_condiciones

urlpatterns = [
    path('', inicio, name='inicio'),
    path('disena-regalo/', disena_regalo, name='disena_regalo'),
    path('producto/<int:producto_id>/', detalle_producto, name='detalle_producto'),
    path('como-comprar/', como_comprar, name='como_comprar'),
    path('preguntas-frecuentes/', preguntas_frecuentes, name='preguntas_frecuentes'),
    path('terminos-y-condiciones/', terminos_condiciones, name='terminos_condiciones'),
    path('aviso-de-privacidad/', aviso_privacidad, name='aviso_privacidad'),
    path('asistente/chat/', assistant_chat, name='assistant_chat'),
]
