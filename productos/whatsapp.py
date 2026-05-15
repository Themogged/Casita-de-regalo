from urllib.parse import quote

from django.conf import settings


DEFAULT_ASSISTANCE_MESSAGE = (
    "Hola, quiero cotizar un detalle de Casita de Regalos. "
    "Me gustaría recibir asesoría para elegir una opción según la ocasión."
)

GENERAL_INFO_MESSAGE = "Hola, quiero información sobre un detalle de Casita de Regalos."
PAYMENT_DATA_MESSAGE = "Hola, quiero los datos de pago."
CATEGORY_INFO_MESSAGE = "Hola, quiero información sobre un detalle de esa categoría."
PERSONALIZATION_MESSAGE = "Hola, quiero cotizar un detalle personalizado."
COVERAGE_INFO_MESSAGE = "Hola, quiero información sobre la cobertura."


def build_whatsapp_url(message, number=None):
    """Build a WhatsApp deep link using the configured business number."""
    phone_number = number or settings.BUSINESS_WHATSAPP_NUMBER
    clean_message = " ".join(str(message or "").split())
    return f"https://wa.me/{phone_number}?text={quote(clean_message)}"
