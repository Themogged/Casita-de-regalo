from django.urls import path

from . import views


urlpatterns = [
    path("", views.memory_center, name="assistant_memory"),
    path("configuracion/", views.update_memory_settings, name="assistant_memory_settings"),
    path("pausar/", views.pause_memory, name="assistant_memory_pause"),
    path("editar/<int:memory_id>/", views.edit_memory, name="assistant_memory_edit"),
    path("eliminar/<int:memory_id>/", views.delete_memory, name="assistant_memory_delete"),
    path("borrar-todo/", views.clear_memory, name="assistant_memory_clear"),
    path("exportar/", views.export_memory, name="assistant_memory_export"),
    path("estado/", views.memory_status, name="assistant_memory_status"),
]
