from io import BytesIO
from zipfile import ZipFile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pedidos.models import Pedido, PedidoItem


class PedidoAdminReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin12345",
        )

        cls.pedido_confirmado = Pedido.objects.create(total=Decimal("81000"), estado="confirmado")
        PedidoItem.objects.create(
            pedido=cls.pedido_confirmado,
            producto_nombre="Desayuno cumpleañero",
            cantidad=1,
            precio=Decimal("81000"),
        )

        cls.pedido_entregado = Pedido.objects.create(total=Decimal("173000"), estado="entregado")
        PedidoItem.objects.create(
            pedido=cls.pedido_entregado,
            producto_nombre="Ramo premium",
            cantidad=1,
            precio=Decimal("173000"),
        )
        PedidoItem.objects.create(
            pedido=cls.pedido_entregado,
            producto_nombre="Mini tarjeta",
            cantidad=2,
            precio=Decimal("5000"),
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_reportes_view_loads_with_summary(self):
        response = self.client.get(reverse("admin:pedidos_pedido_reportes"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reportes de pedidos")
        self.assertContains(response, "Ventas totales")
        self.assertContains(response, "Top productos")

    def test_admin_add_view_loads_without_inline_subtotal_error(self):
        response = self.client.get(reverse("admin:pedidos_pedido_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="pedido_form"', html=False)

    def test_reportes_view_filters_by_estado(self):
        response = self.client.get(
            reverse("admin:pedidos_pedido_reportes"),
            {"estado": "confirmado"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Desayuno cumpleañero")
        self.assertNotContains(response, "Ramo premium")

    def test_export_excel_returns_xlsx_with_rows(self):
        response = self.client.get(reverse("admin:pedidos_pedido_export_excel"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn(".xlsx", response["Content-Disposition"])

        archive = ZipFile(BytesIO(response.content))
        workbook = archive.read("xl/workbook.xml").decode("utf-8")
        resumen_sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        detalle_sheet = archive.read("xl/worksheets/sheet2.xml").decode("utf-8")
        productos_sheet = archive.read("xl/worksheets/sheet3.xml").decode("utf-8")
        pedidos_table = archive.read("xl/tables/table1.xml").decode("utf-8")
        productos_table = archive.read("xl/tables/table2.xml").decode("utf-8")
        styles = archive.read("xl/styles.xml").decode("utf-8")
        self.assertIn("Desayuno cumpleañero", detalle_sheet)
        self.assertIn('name="Panel"', workbook)
        self.assertIn('name="Pedidos"', workbook)
        self.assertIn('name="Productos"', workbook)
        self.assertIn("Reporte de pedidos", resumen_sheet)
        self.assertIn("Ventas", resumen_sheet)
        self.assertIn("Ticket promedio", resumen_sheet)
        self.assertIn("Productos destacados", resumen_sheet)
        self.assertIn("Estado de pedidos", resumen_sheet)
        self.assertIn("showGridLines=\"0\"", resumen_sheet)
        self.assertIn("% ventas", resumen_sheet)
        self.assertIn("Entregado", resumen_sheet)
        self.assertIn("Ramo premium", detalle_sheet)
        self.assertIn("<mergeCells", detalle_sheet)
        self.assertIn("state=\"frozen\"", detalle_sheet)
        self.assertIn("Rendimiento por producto", productos_sheet)
        self.assertIn("Precio promedio COP", productos_sheet)
        self.assertIn("Ingresos COP", productos_sheet)
        self.assertIn("Mini tarjeta", productos_sheet)
        self.assertIn("<tableParts", detalle_sheet)
        self.assertIn("<tableParts", productos_sheet)
        self.assertIn("TablaPedidos", pedidos_table)
        self.assertIn("TablaProductos", productos_table)
        self.assertIn("<autoFilter", pedidos_table)
        self.assertIn("<autoFilter", productos_table)
        self.assertIn("TableStyleMedium4", pedidos_table)
        self.assertIn("numFmtId=\"164\"", styles)
        self.assertIn("numFmtId=\"165\"", styles)
        self.assertIn("FFD7266D", styles)

    def test_export_pdf_of_single_order_returns_file(self):
        response = self.client.get(
            reverse("admin:pedidos_pedido_pdf", args=[self.pedido_confirmado.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(".pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-1.4"))
        self.assertIn(b"CASITA DE REGALOS", response.content)
        self.assertIn(b"Resumen del pedido", response.content)
        self.assertIn(b"Pagina 1 de", response.content)

    def test_export_pdf_report_includes_professional_sections(self):
        response = self.client.get(reverse("admin:pedidos_pedido_export_pdf"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(b"Reporte de pedidos", response.content)
        self.assertIn(b"Resumen comercial", response.content)
        self.assertIn(b"Estado de pedidos", response.content)
        self.assertIn(b"Top productos", response.content)
        self.assertIn(b"Detalle de pedidos", response.content)
