from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import urlencode

from .models import Pedido, PedidoItem
from .reporting import (
    build_excel_bytes,
    build_filename,
    build_pdf_bytes,
    format_cop,
    format_fecha,
    pedido_items_resumen,
    pedido_to_pdf_lines,
    pedido_unidades_totales,
    pedidos_to_pdf_lines,
    pedidos_to_rows,
)


class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    can_delete = False
    fields = ("producto_nombre", "cantidad", "precio_formateado", "subtotal_formateado")
    readonly_fields = fields

    @admin.display(description="Precio")
    def precio_formateado(self, obj):
        return format_cop(obj.precio)

    @admin.display(description="Subtotal")
    def subtotal_formateado(self, obj):
        return format_cop(obj.subtotal())


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    change_list_template = "admin/pedidos/pedido/change_list.html"
    change_form_template = "admin/pedidos/pedido/change_form.html"
    list_display = (
        "id",
        "fecha_resumen",
        "total_formateado",
        "estado",
        "estado_badge",
        "unidades_totales",
        "items_vista_previa",
        "descargar_pdf",
    )
    list_filter = ("estado", "fecha")
    list_editable = ("estado",)
    search_fields = ("id", "items__producto_nombre")
    readonly_fields = ("fecha", "total", "resumen_items", "acciones_pedido")
    fields = ("fecha", "estado", "total", "resumen_items", "acciones_pedido")
    inlines = [PedidoItemInline]
    ordering = ("-fecha",)
    date_hierarchy = "fecha"
    actions = (
        "exportar_seleccion_excel",
        "exportar_seleccion_pdf",
        "marcar_confirmado",
        "marcar_enviado",
        "marcar_entregado",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("items")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "reportes/",
                self.admin_site.admin_view(self.reportes_view),
                name="pedidos_pedido_reportes",
            ),
            path(
                "exportar/excel/",
                self.admin_site.admin_view(self.exportar_excel_view),
                name="pedidos_pedido_export_excel",
            ),
            path(
                "exportar/pdf/",
                self.admin_site.admin_view(self.exportar_pdf_view),
                name="pedidos_pedido_export_pdf",
            ),
            path(
                "<path:object_id>/pdf/",
                self.admin_site.admin_view(self.pedido_pdf_view),
                name="pedidos_pedido_pdf",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Fecha")
    def fecha_resumen(self, obj):
        return format_fecha(timezone.localtime(obj.fecha))

    @admin.display(description="Total")
    def total_formateado(self, obj):
        return format_cop(obj.total)

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        colors = {
            "pendiente": ("#fff1cf", "#7a4f01"),
            "confirmado": ("#dff7e7", "#165a2d"),
            "enviado": ("#dceeff", "#164f86"),
            "entregado": ("#f3e4ff", "#6c2c8f"),
        }
        background, text = colors.get(obj.estado, ("#f3f4f6", "#374151"))
        return format_html(
            '<span style="display:inline-flex;align-items:center;padding:0.35rem 0.7rem;'
            "border-radius:999px;font-weight:700;background:{};color:{};\">{}</span>",
            background,
            text,
            obj.get_estado_display(),
        )

    @admin.display(description="Unidades")
    def unidades_totales(self, obj):
        return pedido_unidades_totales(obj)

    @admin.display(description="Items")
    def items_vista_previa(self, obj):
        resumen = pedido_items_resumen(obj)
        if len(resumen) <= 70:
            return resumen
        return f"{resumen[:67]}..."

    @admin.display(description="PDF")
    def descargar_pdf(self, obj):
        url = reverse("admin:pedidos_pedido_pdf", args=[obj.pk])
        return format_html('<a class="button" href="{}">Descargar</a>', url)

    @admin.display(description="Resumen")
    def resumen_items(self, obj):
        if not obj.pk:
            return "Guarda el pedido para ver sus items."

        items = list(obj.items.all())
        if not items:
            return "Sin items registrados."

        piezas = []
        for item in items:
            piezas.append(
                f"{item.producto_nombre} x{item.cantidad} ({format_cop(item.subtotal())})"
            )
        return " | ".join(piezas)

    @admin.display(description="Acciones")
    def acciones_pedido(self, obj):
        if not obj.pk:
            return "-"

        pdf_url = reverse("admin:pedidos_pedido_pdf", args=[obj.pk])
        reportes_url = reverse("admin:pedidos_pedido_reportes")
        return format_html(
            '<a class="button" href="{}">Descargar PDF</a>&nbsp;'
            '<a class="button" href="{}">Abrir reportes</a>',
            pdf_url,
            reportes_url,
        )

    @admin.action(description="Exportar seleccionados a Excel")
    def exportar_seleccion_excel(self, request, queryset):
        return self._build_excel_response(queryset.order_by("-fecha"), "pedidos-seleccion")

    @admin.action(description="Exportar seleccionados a PDF")
    def exportar_seleccion_pdf(self, request, queryset):
        return self._build_pdf_response(queryset.order_by("-fecha"), "pedidos-seleccion")

    @admin.action(description="Marcar seleccionados como confirmados")
    def marcar_confirmado(self, request, queryset):
        actualizados = queryset.update(estado="confirmado")
        self.message_user(
            request,
            f"{actualizados} pedido(s) actualizados a confirmado.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Marcar seleccionados como enviados")
    def marcar_enviado(self, request, queryset):
        actualizados = queryset.update(estado="enviado")
        self.message_user(
            request,
            f"{actualizados} pedido(s) actualizados a enviado.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Marcar seleccionados como entregados")
    def marcar_entregado(self, request, queryset):
        actualizados = queryset.update(estado="entregado")
        self.message_user(
            request,
            f"{actualizados} pedido(s) actualizados a entregado.",
            level=messages.SUCCESS,
        )

    def reportes_view(self, request):
        filtros = {
            "fecha_desde": request.GET.get("fecha_desde", ""),
            "fecha_hasta": request.GET.get("fecha_hasta", ""),
            "estado": request.GET.get("estado", ""),
            "q": request.GET.get("q", "").strip(),
        }
        queryset = self._queryset_reportes(request, filtros)
        resumen = self._build_resumen(queryset)
        top_productos = self._top_productos(queryset)
        pedidos_recientes = queryset.order_by("-fecha")[:12]
        query_string = self._build_query_string(filtros)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Reportes de pedidos",
            "subtitle": "Resumen comercial, filtros y exportaciones.",
            "filtros": filtros,
            "resumen": resumen,
            "top_productos": top_productos,
            "pedidos_recientes": pedidos_recientes,
            "estados": self.model.ESTADOS,
            "export_excel_url": self._build_export_url(
                "admin:pedidos_pedido_export_excel", query_string
            ),
            "export_pdf_url": self._build_export_url(
                "admin:pedidos_pedido_export_pdf", query_string
            ),
            "changelist_url": reverse("admin:pedidos_pedido_changelist"),
        }
        return TemplateResponse(request, "admin/pedidos/pedido/reportes.html", context)

    def exportar_excel_view(self, request):
        filtros = {
            "fecha_desde": request.GET.get("fecha_desde", ""),
            "fecha_hasta": request.GET.get("fecha_hasta", ""),
            "estado": request.GET.get("estado", ""),
            "q": request.GET.get("q", "").strip(),
        }
        queryset = self._queryset_reportes(request, filtros).order_by("-fecha")
        return self._build_excel_response(queryset, "reporte-pedidos")

    def exportar_pdf_view(self, request):
        filtros = {
            "fecha_desde": request.GET.get("fecha_desde", ""),
            "fecha_hasta": request.GET.get("fecha_hasta", ""),
            "estado": request.GET.get("estado", ""),
            "q": request.GET.get("q", "").strip(),
        }
        queryset = self._queryset_reportes(request, filtros).order_by("-fecha")
        return self._build_pdf_response(queryset, "reporte-pedidos")

    def pedido_pdf_view(self, request, object_id):
        pedido = self.get_object(request, object_id)
        if pedido is None:
            raise Http404("Pedido no encontrado.")

        filename = build_filename("pedido", f"#{pedido.pk}", "pdf")
        pdf_bytes = build_pdf_bytes(
            f"Pedido #{pedido.pk}",
            "Casita de Regalos",
            pedido_to_pdf_lines(pedido),
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _build_excel_response(self, queryset, prefix):
        queryset = queryset.prefetch_related("items")
        rows = pedidos_to_rows(queryset)
        excel_bytes = build_excel_bytes(
            "Pedidos",
            ["Pedido", "Fecha", "Estado", "Unidades", "Total COP", "Items"],
            rows,
        )
        filename = build_filename(prefix, timezone.localdate().isoformat(), "xlsx")
        response = HttpResponse(
            excel_bytes,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _build_pdf_response(self, queryset, prefix):
        queryset = queryset.prefetch_related("items")
        resumen = self._build_resumen(queryset)
        lines = [
            f"Pedidos encontrados: {resumen['pedidos_total']}",
            f"Ventas totales: {format_cop(resumen['ventas_totales'])}",
            f"Unidades vendidas: {resumen['unidades_totales']}",
            "",
        ]
        lines.extend(pedidos_to_pdf_lines(queryset))

        pdf_bytes = build_pdf_bytes(
            "Reporte de pedidos",
            "Casita de Regalos",
            lines,
        )
        filename = build_filename(prefix, timezone.localdate().isoformat(), "pdf")
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _queryset_reportes(self, request, filtros):
        queryset = self.get_queryset(request)

        if filtros["fecha_desde"]:
            queryset = queryset.filter(fecha__date__gte=filtros["fecha_desde"])
        if filtros["fecha_hasta"]:
            queryset = queryset.filter(fecha__date__lte=filtros["fecha_hasta"])
        if filtros["estado"]:
            queryset = queryset.filter(estado=filtros["estado"])

        query = filtros["q"]
        if query:
            condition = Q(items__producto_nombre__icontains=query)
            if query.isdigit():
                condition |= Q(pk=int(query))
            queryset = queryset.filter(condition).distinct()

        return queryset

    def _build_resumen(self, queryset):
        pedidos_total = queryset.count()
        ventas_totales = queryset.aggregate(total=Sum("total"))["total"] or Decimal("0")
        unidades_totales = (
            PedidoItem.objects.filter(pedido__in=queryset).aggregate(total=Sum("cantidad"))[
                "total"
            ]
            or 0
        )
        estado_totales = []
        for estado, etiqueta in self.model.ESTADOS:
            cantidad = queryset.filter(estado=estado).count()
            estado_totales.append({"key": estado, "label": etiqueta, "count": cantidad})

        return {
            "pedidos_total": pedidos_total,
            "ventas_totales": ventas_totales,
            "unidades_totales": unidades_totales,
            "estado_totales": estado_totales,
        }

    def _top_productos(self, queryset):
        revenue_expression = ExpressionWrapper(
            F("cantidad") * F("precio"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        top_productos = list(
            PedidoItem.objects.filter(pedido__in=queryset)
            .values("producto_nombre")
            .annotate(unidades=Sum("cantidad"), ingresos=Sum(revenue_expression))
            .order_by("-unidades", "producto_nombre")[:8]
        )

        max_unidades = max((producto["unidades"] for producto in top_productos), default=1)
        for producto in top_productos:
            producto["barra"] = max(12, round((producto["unidades"] / max_unidades) * 100))
        return top_productos

    def _build_export_url(self, name, query_string):
        base_url = reverse(name)
        if not query_string:
            return base_url
        return f"{base_url}?{query_string}"

    def _build_query_string(self, filtros):
        clean_filters = {key: value for key, value in filtros.items() if value}
        return urlencode(clean_filters)
