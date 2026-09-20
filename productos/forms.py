from django import forms

from .models import Producto, VideoElaboracion


class ProductoAdminForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = "__all__"
        widgets = {
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 7,
                    "placeholder": "Explica qué incluye el regalo, materiales y opciones de personalización.",
                }
            ),
            "imagen": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
        }
        help_texts = {
            "nombre": "Usa un nombre corto y fácil de reconocer en el catálogo.",
            "descripcion": "Esta información ayuda al cliente a entender exactamente qué recibirá.",
            "precio": "Valor base en pesos colombianos, sin puntos ni símbolo de moneda.",
            "stock": "Usa 0 para mostrar el producto como agotado.",
            "destacado": "Los productos destacados aparecen primero y pueden mostrarse en la portada.",
            "imagen": "Recomendado: imagen vertical, nítida y en JPG, PNG o WebP.",
        }

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if not nombre:
            raise forms.ValidationError("Escribe un nombre para identificar el producto.")
        return nombre

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor que cero.")
        return precio


class VideoElaboracionAdminForm(forms.ModelForm):
    class Meta:
        model = VideoElaboracion
        fields = "__all__"
        widgets = {
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Describe brevemente qué se está elaborando en el video.",
                }
            ),
            "video": forms.ClearableFileInput(
                attrs={"accept": "video/mp4,video/webm,video/quicktime"}
            ),
            "portada": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
        }
        help_texts = {
            "titulo": "Nombre interno y texto visible en la sección de elaboración.",
            "descripcion": "Una frase corta sobre el proceso mostrado.",
            "video": "MP4, WebM o MOV de máximo 30 MB. Para mayor compatibilidad usa MP4 H.264.",
            "portada": "Opcional. Usa una imagen vertical; si existe una portada generada se utilizará automáticamente.",
            "activo": "Solo los videos activos pueden aparecer en la tienda.",
            "destacado": "Prioriza este video dentro de la sección de elaboración.",
            "orden": "Los números menores aparecen primero.",
        }

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"].strip()
        if not titulo:
            raise forms.ValidationError("Escribe un título para identificar el video.")
        return titulo
