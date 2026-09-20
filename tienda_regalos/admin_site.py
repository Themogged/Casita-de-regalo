from django.contrib.admin import AdminSite
from django.db import DatabaseError
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone


class CasitaAdminSite(AdminSite):
    site_header = "Casita de Regalos"
    site_title = "Casita de Regalos"
    index_title = "Centro de gestión"
    index_template = "admin/index.html"

    app_order = {
        "productos": 10,
        "pedidos": 20,
        "asistente": 30,
        "carrito": 40,
        "auth": 50,
    }
    model_order = {
        "productos": {
            "producto": 10,
            "videoelaboracion": 20,
            "categoria": 30,
        },
        "pedidos": {"pedido": 10},
    }
    app_names = {
        "productos": "Catálogo y contenido",
        "pedidos": "Pedidos y reportes",
        "asistente": "Asistente Cora",
        "carrito": "Listas de clientes",
        "auth": "Usuarios y accesos",
    }

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        for app in app_list:
            app["name"] = self.app_names.get(app["app_label"], app["name"])
            order = self.model_order.get(app["app_label"], {})
            app["models"].sort(
                key=lambda model: (
                    order.get(model["object_name"].lower(), 999),
                    model["name"].casefold(),
                )
            )
        app_list.sort(
            key=lambda app: (
                self.app_order.get(app["app_label"], 999),
                app["name"].casefold(),
            )
        )
        return app_list

    def index(self, request, extra_context=None):
        context = {
            "dashboard_stats": {},
            "dashboard_attention": [],
            "dashboard_quick_actions": self._quick_actions(request),
            "dashboard_ready": False,
        }
        try:
            from pedidos.models import Pedido
            from productos.models import Producto, VideoElaboracion

            product_stats = Producto.objects.aggregate(
                total=Count("id"),
                available=Count("id", filter=Q(stock__gt=3)),
                low_stock=Count("id", filter=Q(stock__gt=0, stock__lte=3)),
                out_of_stock=Count("id", filter=Q(stock=0)),
                without_image=Count("id", filter=Q(imagen="") | Q(imagen__isnull=True)),
            )
            video_stats = VideoElaboracion.objects.aggregate(
                total=Count("id"),
                active=Count("id", filter=Q(activo=True)),
                featured=Count("id", filter=Q(destacado=True)),
            )
            video_stats["missing_files"] = sum(
                1
                for item in VideoElaboracion.objects.only("video")
                if not self._stored_file_exists(item.video)
            )
            today = timezone.localdate()
            order_stats = Pedido.objects.aggregate(
                pending=Count("id", filter=Q(estado="pendiente")),
                today=Count("id", filter=Q(fecha__date=today)),
            )

            context["dashboard_stats"] = {
                "products": product_stats["total"],
                "available": product_stats["available"],
                "active_videos": video_stats["active"],
                "pending_orders": order_stats["pending"],
                "today_orders": order_stats["today"],
            }
            context["dashboard_attention"] = self._attention_items(
                product_stats,
                video_stats,
                order_stats,
            )
            context["dashboard_ready"] = True
        except DatabaseError:
            # The regular application list remains usable during initial migrations.
            pass

        if extra_context:
            context.update(extra_context)
        return super().index(request, extra_context=context)

    @staticmethod
    def _quick_actions(request):
        actions = []
        definitions = (
            (
                "productos.add_producto",
                "Nuevo producto",
                "Añade una referencia al catálogo.",
                "admin:productos_producto_add",
                "primary",
            ),
            (
                "productos.add_videoelaboracion",
                "Nuevo video",
                "Publica un proceso de elaboración.",
                "admin:productos_videoelaboracion_add",
                "soft",
            ),
            (
                "pedidos.view_pedido",
                "Revisar pedidos",
                "Gestiona estados y exportaciones.",
                "admin:pedidos_pedido_changelist",
                "neutral",
            ),
            (
                "pedidos.view_pedido",
                "Abrir reportes",
                "Consulta el resumen comercial.",
                "admin:pedidos_pedido_reportes",
                "neutral",
            ),
        )
        for permission, label, description, route, tone in definitions:
            if request.user.has_perm(permission):
                actions.append(
                    {
                        "label": label,
                        "description": description,
                        "url": reverse(route),
                        "tone": tone,
                    }
                )
        return actions

    @staticmethod
    def _attention_items(product_stats, video_stats, order_stats):
        definitions = (
            (
                product_stats["low_stock"],
                "Productos con stock bajo",
                "Conviene revisar estas referencias antes de recibir nuevas cotizaciones.",
                f'{reverse("admin:productos_producto_changelist")}?disponibilidad=bajo',
                "warning",
            ),
            (
                product_stats["out_of_stock"],
                "Productos agotados",
                "No aparecen como disponibles en la tienda.",
                f'{reverse("admin:productos_producto_changelist")}?disponibilidad=agotado',
                "danger",
            ),
            (
                product_stats["without_image"],
                "Productos sin imagen",
                "Completa la imagen principal para mejorar el catálogo.",
                f'{reverse("admin:productos_producto_changelist")}?imagen_estado=sin_imagen',
                "warning",
            ),
            (
                order_stats["pending"],
                "Pedidos pendientes",
                "Necesitan confirmación o actualización de estado.",
                f'{reverse("admin:pedidos_pedido_changelist")}?estado__exact=pendiente',
                "primary",
            ),
            (
                video_stats["missing_files"],
                "Videos con archivo faltante",
                "El registro existe, pero el archivo debe volver a cargarse.",
                reverse("admin:productos_videoelaboracion_changelist"),
                "danger",
            ),
            (
                max(video_stats["total"] - video_stats["active"], 0),
                "Videos inactivos",
                "Puedes revisarlos y activarlos cuando estén listos.",
                f'{reverse("admin:productos_videoelaboracion_changelist")}?activo__exact=0',
                "neutral",
            ),
        )
        return [
            {
                "count": count,
                "label": label,
                "description": description,
                "url": url,
                "tone": tone,
            }
            for count, label, description, url, tone in definitions
            if count
        ]

    @staticmethod
    def _stored_file_exists(field_file):
        if not field_file or not field_file.name:
            return False
        try:
            return field_file.storage.exists(field_file.name)
        except (OSError, ValueError):
            return False
