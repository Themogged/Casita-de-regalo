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
        worksheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("Desayuno cumpleañero", worksheet)
        self.assertIn("Ramo premium", worksheet)

    def test_export_pdf_of_single_order_returns_file(self):
        response = self.client.get(
            reverse("admin:pedidos_pedido_pdf", args=[self.pedido_confirmado.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(".pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-1.4"))
