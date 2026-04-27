import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .assistant_service import get_assistant_reply


@require_POST
def assistant_chat(request):
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

    reply = get_assistant_reply(message, history=history)
    return JsonResponse(
        {
            "ok": True,
            "reply": reply["message"],
            "mode": reply["mode"],
            "configured": reply["configured"],
            "actions": reply.get("actions", []),
        }
    )
