from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    destacado = models.BooleanField(default=False)  # Para mostrar en portada
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    @property
    def disponible(self):
        return self.stock > 0

    @property
    def stock_label(self):
        if self.stock <= 0:
            return 'Agotado'
        if self.stock <= 3:
            return f'Ultimas {self.stock} unidades'
        return 'Disponible'

    @property
    def stock_badge_class(self):
        if self.stock <= 0:
            return 'stock-badge stock-badge--out'
        if self.stock <= 3:
            return 'stock-badge stock-badge--low'
        return 'stock-badge stock-badge--ok'

    class Meta:
        ordering = ['-destacado', 'nombre']
