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

    @property
    def public_status_label(self):
        if self.stock <= 0:
            return 'Agotado'
        return 'Disponible'

    @property
    def public_status_badge_class(self):
        if self.stock <= 0:
            return 'stock-badge stock-badge--out'
        return 'stock-badge stock-badge--ok'

    class Meta:
        ordering = ['-destacado', 'nombre']


class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/galeria/')
    titulo = models.CharField(max_length=120, blank=True)
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.titulo or f'Imagen de {self.producto.nombre}'

    class Meta:
        ordering = ['orden', 'id']


class InteraccionCliente(models.Model):
    TIPO_WHATSAPP = 'whatsapp'
    TIPO_INSTAGRAM = 'instagram'
    TIPO_CARRITO = 'carrito'
    TIPO_CATALOGO = 'catalogo'
    TIPO_OTRO = 'otro'

    TIPO_CHOICES = [
        (TIPO_WHATSAPP, 'WhatsApp'),
        (TIPO_INSTAGRAM, 'Instagram'),
        (TIPO_CARRITO, 'Carrito'),
        (TIPO_CATALOGO, 'Catalogo'),
        (TIPO_OTRO, 'Otro'),
    ]

    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES, default=TIPO_OTRO)
    etiqueta = models.CharField(max_length=120, blank=True)
    destino = models.URLField(max_length=500, blank=True)
    pagina = models.CharField(max_length=300, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.etiqueta or "sin etiqueta"}'

    class Meta:
        ordering = ['-creado']
        verbose_name = 'interaccion de cliente'
        verbose_name_plural = 'interacciones de clientes'
