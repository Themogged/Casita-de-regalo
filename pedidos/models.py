from decimal import Decimal

from django.conf import settings
from django.db import models


class Pedido(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="pedidos",
        blank=True,
        null=True,
    )
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    detalles_personalizacion = models.JSONField(default=dict, blank=True)

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),  # 🔥 agregado (recomendado)
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
    ]

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    def __str__(self):
        return f"Pedido #{self.id} - ${self.total}"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto_nombre = models.CharField(max_length=200)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    personalizacion = models.JSONField(default=dict, blank=True)

    def subtotal(self):
        cantidad = self.cantidad or 0
        precio = self.precio if self.precio is not None else Decimal("0")
        return cantidad * precio
