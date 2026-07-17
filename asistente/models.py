from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class AssistantProfile(models.Model):
    DEFAULT_CATEGORIES = [
        "identity",
        "preferences",
        "people",
        "dates",
        "budget",
        "products",
        "personalization",
        "sizes",
        "delivery",
        "payment",
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_profile",
    )
    memory_enabled = models.BooleanField(default=False)
    memory_paused_until = models.DateTimeField(blank=True, null=True)
    allowed_categories = models.JSONField(default=list, blank=True)
    conversation_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_memory_active(self):
        if not self.memory_enabled:
            return False
        return not self.memory_paused_until or self.memory_paused_until <= timezone.now()

    def category_is_allowed(self, category):
        return category in self.allowed_categories

    def __str__(self):
        return f"Memoria de {self.user.get_username()}"

    class Meta:
        verbose_name = "perfil de memoria"
        verbose_name_plural = "perfiles de memoria"


class AssistantMemory(models.Model):
    class MemoryType(models.TextChoices):
        OBSERVATION = "observation", "Dato confirmado"
        PREFERENCE = "preference", "Preferencia"
        PERMANENT = "permanent", "Instrucción permanente"
        TEMPORARY = "temporary", "Información temporal"

    class Category(models.TextChoices):
        IDENTITY = "identity", "Identidad"
        PREFERENCES = "preferences", "Preferencias"
        PEOPLE = "people", "Personas importantes"
        DATES = "dates", "Fechas especiales"
        BUDGET = "budget", "Presupuesto"
        PRODUCTS = "products", "Productos"
        PERSONALIZATION = "personalization", "Personalizaciones"
        SIZES = "sizes", "Tallas o medidas"
        DELIVERY = "delivery", "Entrega"
        PAYMENT = "payment", "Forma de pago"
        OTHER = "other", "Otros"

    class Source(models.TextChoices):
        CHAT = "chat", "Conversación"
        PROFILE = "profile", "Perfil"
        PURCHASE = "purchase", "Compra"
        MANUAL = "manual", "Edición manual"

    class Consent(models.TextChoices):
        PENDING = "pending", "Pendiente"
        GRANTED = "granted", "Autorizado"
        DENIED = "denied", "Rechazado"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_memories",
    )
    category = models.CharField(max_length=32, choices=Category.choices)
    key = models.SlugField(max_length=90)
    content = models.CharField(max_length=600)
    search_text = models.CharField(max_length=900, blank=True)
    embedding = models.JSONField(default=list, blank=True)
    importance = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    memory_type = models.CharField(
        max_length=20,
        choices=MemoryType.choices,
        default=MemoryType.OBSERVATION,
    )
    mention_count = models.PositiveSmallIntegerField(default=1)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.CHAT)
    consent_status = models.CharField(
        max_length=16,
        choices=Consent.choices,
        default=Consent.GRANTED,
    )
    is_sensitive = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())

    def __str__(self):
        return f"{self.get_category_display()}: {self.content[:50]}"

    class Meta:
        ordering = ["-importance", "-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "key"], name="unique_memory_key_per_user"),
        ]
        indexes = [
            models.Index(fields=["user", "category", "consent_status"]),
            models.Index(fields=["user", "updated_at"]),
        ]
        verbose_name = "recuerdo del asistente"
        verbose_name_plural = "recuerdos del asistente"


class AssistantConversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_conversations",
    )
    title = models.CharField(max_length=160, blank=True)
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Conversación {self.pk}"

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "is_active", "updated_at"])]
        verbose_name = "conversación del asistente"
        verbose_name_plural = "conversaciones del asistente"


class AssistantMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Usuario"
        ASSISTANT = "assistant", "Asistente"

    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]
        verbose_name = "mensaje del asistente"
        verbose_name_plural = "mensajes del asistente"
