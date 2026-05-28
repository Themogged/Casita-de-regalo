from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

MAX_VIDEO_SIZE_MB = 30


def validate_video_size(video_file):
    if video_file.size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise ValidationError(f'El video no debe superar {MAX_VIDEO_SIZE_MB} MB.')


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
            return f'Últimas {self.stock} unidades'
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


class VideoElaboracion(models.Model):
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    video = models.FileField(
        upload_to='procesos/videos/',
        validators=[FileExtensionValidator(['mp4', 'webm', 'mov']), validate_video_size],
        help_text=f'Formatos permitidos: MP4, WEBM o MOV. Tamaño máximo: {MAX_VIDEO_SIZE_MB} MB.',
    )
    portada = models.ImageField(upload_to='procesos/portadas/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    @property
    def mime_type(self):
        extension = self.video.name.rsplit('.', 1)[-1].lower()
        return {
            'webm': 'video/webm',
            'mov': 'video/quicktime',
        }.get(extension, 'video/mp4')

    class Meta:
        ordering = ['orden', '-destacado', '-fecha_creacion']
        indexes = [
            models.Index(fields=['activo', 'orden']),
        ]
        verbose_name = 'video de elaboración'
        verbose_name_plural = 'videos de elaboración'
