from django.urls import path
from .views import productos_por_categoria

urlpatterns = [
    path('<int:categoria_id>/', productos_por_categoria, name='categoria'),
]