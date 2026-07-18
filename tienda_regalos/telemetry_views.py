import hashlib
import json
import logging
from urllib.parse import urlsplit

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .middleware import client_ip


logger = logging.getLogger("storefront.events")
ALLOWED_EVENTS = {
    "page_view",
    "product_view",
    "cart_add",
    "cart_open",
    "product_personalized",
    "quote_start",
    "quote_complete",
    "form_submitted",
    "form_error",
    "assistant_interaction",
    "auth_view",
    "auth_submit",
    "client_error",
    "media_error",
    "server_error",
}
ALLOWED_CONTEXT_KEYS = {"source", "component", "code", "status", "mode"}


def _safe_path(value):
    path = urlsplit(str(value or "")).path[:240]
    return path if path.startswith("/") else "/"


@require_POST
def collect_event(request):
    if int(request.META.get("CONTENT_LENGTH") or 0) > 4096:
        return JsonResponse({"ok": False}, status=413)
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False}, status=400)

    event_name = str(payload.get("event", "")).strip()
    if event_name not in ALLOWED_EVENTS:
        return JsonResponse({"ok": False}, status=400)

    ip_hash = hashlib.sha256(
        f"{settings.SECRET_KEY}:{client_ip(request)}".encode("utf-8")
    ).hexdigest()[:16]
    rate_key = f"telemetry:{ip_hash}"
    count = cache.get(rate_key, 0) + 1
    cache.set(rate_key, count, timeout=60)
    if count > settings.TELEMETRY_EVENTS_PER_MINUTE:
        return JsonResponse({"ok": False}, status=429)

    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    safe_context = {
        key: str(value)[:80]
        for key, value in context.items()
        if key in ALLOWED_CONTEXT_KEYS and isinstance(value, (str, int, float, bool))
    }
    product_id = payload.get("product_id")
    try:
        product_id = int(product_id) if product_id not in (None, "") else None
    except (TypeError, ValueError):
        product_id = None

    logger.info(
        json.dumps(
            {
                "event": event_name,
                "path": _safe_path(payload.get("path") or request.path),
                "product_id": product_id,
                "context": safe_context,
                "visitor": ip_hash,
                "authenticated": request.user.is_authenticated,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )
    return JsonResponse({"ok": True}, status=202)
