from decimal import Decimal

from django.db import models


class Pedido(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

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

    def subtotal(self):
        cantidad = self.cantidad or 0
        precio = self.precio if self.precio is not None else Decimal("0")
        return cantidad * precio
