from django.urls import path

from .assistant_views import assistant_chat
from .views import detalle_producto, inicio

urlpatterns = [
    path('', inicio, name='inicio'),
    path('producto/<int:producto_id>/', detalle_producto, name='detalle_producto'),
    path('asistente/chat/', assistant_chat, name='assistant_chat'),
]
