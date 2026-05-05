import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import InteraccionCliente


TIPOS_PERMITIDOS = {
    InteraccionCliente.TIPO_WHATSAPP,
    InteraccionCliente.TIPO_INSTAGRAM,
    InteraccionCliente.TIPO_CARRITO,
    InteraccionCliente.TIPO_CATALOGO,
}


def _clean_text(value, max_length):
    if not isinstance(value, str):
        return ''
    return value.strip()[:max_length]


@require_POST
def registrar_interaccion(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'payload_invalido'}, status=400)

    tipo = _clean_text(payload.get('tipo'), 40) or InteraccionCliente.TIPO_OTRO
    if tipo not in TIPOS_PERMITIDOS:
        tipo = InteraccionCliente.TIPO_OTRO

    InteraccionCliente.objects.create(
        tipo=tipo,
        etiqueta=_clean_text(payload.get('etiqueta'), 120),
        destino=_clean_text(payload.get('destino'), 500),
        pagina=_clean_text(payload.get('pagina'), 300),
        user_agent=_clean_text(request.META.get('HTTP_USER_AGENT', ''), 300),
    )

    return JsonResponse({'ok': True})
