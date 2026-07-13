import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .assistant_service import get_assistant_reply


@require_POST
def assistant_chat(request):
    raw_content_length = str(request.META.get("CONTENT_LENGTH") or "")
    content_length = int(raw_content_length) if raw_content_length.isdigit() else 0
    if content_length > 24_000:
        return JsonResponse(
            {
                "ok": False,
                "message": "El mensaje enviado es demasiado grande.",
            },
            status=413,
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse(
            {
                "ok": False,
                "message": "No pudimos leer el mensaje enviado al asistente.",
            },
            status=400,
        )

    if not isinstance(payload, dict):
        return JsonResponse(
            {
                "ok": False,
                "message": "El formato del mensaje no es válido.",
            },
            status=400,
        )

    message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])

    if not message:
        return JsonResponse(
            {
                "ok": False,
                "message": "Escribe una pregunta para que el asistente pueda ayudarte.",
            },
            status=400,
        )

    if len(message) > 500:
        return JsonResponse(
            {
                "ok": False,
                "message": "La pregunta es demasiado larga. Resúmela en máximo 500 caracteres.",
            },
            status=400,
        )

    reply = get_assistant_reply(
        message,
        history=history if isinstance(history, list) else [],
        cart=request.session.get("carrito", {}),
    )
    return JsonResponse(
        {
            "ok": True,
            "reply": reply["message"],
            "mode": reply["mode"],
            "configured": reply["configured"],
            "actions": reply.get("actions", []),
        }
    )
