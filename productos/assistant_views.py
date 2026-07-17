import json

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from asistente.memory import (
    MemoryCandidate,
    build_memory_context,
    contains_sensitive_data,
    extract_memory_candidate,
    get_memory_profile,
    normalize_text,
    redact_sensitive_content,
    record_conversation_turn,
    retrieve_relevant_memories,
    save_memory_candidate,
    serialize_memory,
)

from .assistant_service import get_assistant_reply


MAX_BODY_BYTES = 24_000
MAX_MESSAGE_LENGTH = 500
MAX_SESSION_HISTORY = 40
RATE_LIMIT = 40
RATE_WINDOW_SECONDS = 60


def _error(message, status=400):
    return JsonResponse({"ok": False, "message": message}, status=status)


def _rate_limit_key(request):
    identity = request.user.pk if request.user.is_authenticated else request.session.session_key
    if not identity:
        request.session.create()
        identity = request.session.session_key
    return f"assistant-rate:{identity}"


def _is_rate_limited(request):
    key = _rate_limit_key(request)
    try:
        current = cache.incr(key)
    except ValueError:
        cache.set(key, 1, RATE_WINDOW_SECONDS)
        current = 1
    return current > RATE_LIMIT


def _sanitize_page_context(raw_context):
    if not isinstance(raw_context, dict):
        return {}
    allowed = {
        "path": 180,
        "page_title": 180,
        "product_id": 20,
        "product_name": 180,
        "category": 100,
        "selected_options": 500,
    }
    context = {}
    for key, limit in allowed.items():
        value = str(raw_context.get(key, "")).strip()
        if value:
            context[key] = value[:limit]
    return context


def _session_history(request):
    history = request.session.get("assistant_history", [])
    return [item for item in history if isinstance(item, dict)][-MAX_SESSION_HISTORY:]


def _store_session_turn(request, user_message, assistant_message):
    history = _session_history(request)
    history.extend(
        [
            {"role": "user", "text": redact_sensitive_content(user_message)[:900]},
            {"role": "assistant", "text": redact_sensitive_content(assistant_message)[:900]},
        ]
    )
    request.session["assistant_history"] = history[-MAX_SESSION_HISTORY:]
    request.session.modified = True


def _candidate_from_session(raw):
    if not isinstance(raw, dict):
        return None
    required = {"category", "key", "content"}
    if not required.issubset(raw):
        return None
    return MemoryCandidate(
        category=str(raw["category"]),
        key=str(raw["key"]),
        content=str(raw["content"]),
        importance=int(raw.get("importance", 3)),
        is_sensitive=bool(raw.get("is_sensitive", False)),
        memory_type=str(raw.get("memory_type", "observation")),
    )


def _candidate_to_session(candidate):
    return {
        "category": candidate.category,
        "key": candidate.key,
        "content": candidate.content,
        "importance": candidate.importance,
        "is_sensitive": candidate.is_sensitive,
        "memory_type": candidate.memory_type,
    }


def _handle_pending_memory(request, normalized_message):
    pending = _candidate_from_session(request.session.get("assistant_pending_memory"))
    if not pending:
        return None

    accepts = any(value in normalized_message for value in ("si guard", "sí guard", "autoriz", "actualiza"))
    rejects = any(value in normalized_message for value in ("no guard", "no recuer", "conserva", "cancel"))
    if not (accepts or rejects):
        return None

    request.session.pop("assistant_pending_memory", None)
    request.session.modified = True
    if rejects:
        return {
            "reply": "Entendido. No cambié ni guardé ese dato.",
            "memory_event": "cancelled",
        }

    result = save_memory_candidate(request.user, pending, force=True, consent_granted=True)
    return {
        "reply": "Listo. Guardé ese dato y podrás verlo o eliminarlo desde Memoria del asistente.",
        "memory_event": result["status"],
    }


def _recent_order_context(request):
    if not request.user.is_authenticated:
        return []
    return [
        {
            "id": order.pk,
            "status": order.estado,
            "status_label": order.get_estado_display(),
            "created_at": order.fecha.isoformat(),
            "delivery_date": order.fecha_entrega.isoformat() if order.fecha_entrega else "",
            "delivery_label": order.fecha_entrega.strftime("%d/%m/%Y") if order.fecha_entrega else "",
        }
        for order in request.user.pedidos.order_by("-fecha")[:3]
    ]


def _build_extra_context(page_context, memories, recent_orders, conversation_summary=""):
    parts = []
    memory_context = build_memory_context(memories)
    if memory_context:
        parts.append(memory_context)
    if page_context:
        visible = ", ".join(f"{key}: {value}" for key, value in page_context.items())
        parts.append(f"Página visible ahora: {visible}.")
    if recent_orders:
        order_text = "; ".join(
            f"pedido {order['id']}, estado {order['status_label']}" for order in recent_orders
        )
        parts.append(f"Pedidos recientes del usuario autenticado: {order_text}.")
    if conversation_summary:
        parts.append(
            "Resumen autorizado de la conversación extensa: "
            f"{conversation_summary[:3500]}"
        )
    return "\n".join(parts)


@require_POST
def assistant_chat(request):
    raw_content_length = str(request.META.get("CONTENT_LENGTH") or "")
    content_length = int(raw_content_length) if raw_content_length.isdigit() else 0
    if content_length > MAX_BODY_BYTES:
        return _error("El mensaje enviado es demasiado grande.", status=413)
    if _is_rate_limited(request):
        return _error("Espera un momento antes de enviar otro mensaje.", status=429)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _error("No pudimos leer el mensaje enviado al asistente.")
    if not isinstance(payload, dict):
        return _error("El formato del mensaje no es válido.")

    message = str(payload.get("message", "")).strip()
    if not message:
        return _error("Escribe una pregunta para que el asistente pueda ayudarte.")
    if len(message) > MAX_MESSAGE_LENGTH:
        return _error("La pregunta es demasiado larga. Resúmela en máximo 500 caracteres.")
    if contains_sensitive_data(message):
        return _error(
            "Por seguridad, no envíes contraseñas, códigos ni datos completos de tarjetas. "
            "Cora no necesita esa información para ayudarte."
        )

    private_session = bool(payload.get("private_session", False))
    page_context = _sanitize_page_context(payload.get("context"))
    browser_history = payload.get("history", [])
    history = [] if private_session else _session_history(request)
    if (private_session or not history) and isinstance(browser_history, list):
        history = browser_history[-MAX_SESSION_HISTORY:]

    memories = []
    profile = None
    memory_event = "unavailable"
    if request.user.is_authenticated and not private_session:
        profile = get_memory_profile(request.user)
        memory_event = "disabled" if not profile.is_memory_active else "idle"
        pending_response = _handle_pending_memory(request, normalize_text(message))
        if pending_response:
            _store_session_turn(request, message, pending_response["reply"])
            return JsonResponse(
                {
                    "ok": True,
                    "reply": pending_response["reply"],
                    "mode": "memory",
                    "configured": False,
                    "actions": [],
                    "memory_event": pending_response["memory_event"],
                }
            )

        candidate = extract_memory_candidate(message) if profile.is_memory_active else None
        if candidate:
            if candidate.is_sensitive:
                request.session["assistant_pending_memory"] = _candidate_to_session(candidate)
                request.session.modified = True
                reply = (
                    f"Puedo recordar “{candidate.content}”, pero es un dato privado. "
                    "¿Quieres autorizar que lo guarde? Puedes responder “sí, guardar” o “no guardar”."
                )
                _store_session_turn(request, message, reply)
                return JsonResponse(
                    {
                        "ok": True,
                        "reply": reply,
                        "mode": "memory",
                        "configured": False,
                        "actions": [
                            {"label": "Sí, guardar", "prompt": "Sí, guardar"},
                            {"label": "No guardar", "prompt": "No guardar"},
                        ],
                        "memory_event": "consent_required",
                    }
                )
            result = save_memory_candidate(request.user, candidate)
            memory_event = result["status"]
            if result["status"] == "conflict":
                request.session["assistant_pending_memory"] = _candidate_to_session(candidate)
                request.session.modified = True
                reply = (
                    f"Tengo guardado “{result['memory'].content}” y ahora mencionas “{candidate.content}”. "
                    "¿Quieres conservar el anterior o actualizarlo?"
                )
                _store_session_turn(request, message, reply)
                return JsonResponse(
                    {
                        "ok": True,
                        "reply": reply,
                        "mode": "memory",
                        "configured": False,
                        "actions": [
                            {"label": "Actualizar", "prompt": "Sí, actualizar"},
                            {"label": "Conservar", "prompt": "Conservar el anterior"},
                        ],
                        "memory_event": "conflict",
                    }
                )
        memories = retrieve_relevant_memories(request.user, message)

    recent_orders = _recent_order_context(request)
    conversation_summary = (
        profile.conversation_summary
        if profile and profile.is_memory_active
        else ""
    )
    assistant_context = _build_extra_context(
        page_context,
        memories,
        recent_orders,
        conversation_summary,
    )
    memory_facts = [serialize_memory(memory) for memory in memories]
    reply = get_assistant_reply(
        message,
        history=history,
        cart=request.session.get("carrito", {}),
        assistant_context=assistant_context,
        memory_facts=memory_facts,
        page_context=page_context,
        order_context=recent_orders,
    )

    if not private_session:
        _store_session_turn(request, message, reply["message"])
        if request.user.is_authenticated:
            record_conversation_turn(request.user, message, reply["message"])

    return JsonResponse(
        {
            "ok": True,
            "reply": reply["message"],
            "mode": reply["mode"],
            "configured": reply["configured"],
            "actions": reply.get("actions", []),
            "memory_event": memory_event,
        }
    )
