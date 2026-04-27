import json
import os
from urllib import error, request

from django.db.models import Count
from django.urls import reverse

from .models import Categoria, Producto


class AssistantProviderError(Exception):
    pass


def _normalize_text(value):
    replacements = str.maketrans(
        {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "Á": "a",
            "É": "e",
            "Í": "i",
            "Ó": "o",
            "Ú": "u",
            "ñ": "n",
            "Ñ": "n",
        }
    )
    return (value or "").translate(replacements).strip().lower()


def _format_cop(value):
    return f"${int(value):,} COP".replace(",", ".")


def _get_openai_api_key():
    return os.getenv("OPENAI_API_KEY", "").strip()


def _get_openai_model():
    return os.getenv("OPENAI_ASSISTANT_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"


def _serialize_catalog_context():
    categorias = (
        Categoria.objects.annotate(total_productos=Count("producto"))
        .filter(total_productos__gt=0)
        .order_by("nombre")
    )
    destacados = (
        Producto.objects.select_related("categoria")
        .filter(stock__gt=0)
        .order_by("-destacado", "precio", "nombre")[:14]
    )

    category_lines = []
    for categoria in categorias:
        ejemplos = list(
            Producto.objects.filter(categoria=categoria, stock__gt=0)
            .order_by("-destacado", "precio", "nombre")
            .values_list("nombre", flat=True)[:4]
        )
        if ejemplos:
            category_lines.append(
                f"- {categoria.nombre}: {categoria.total_productos} referencias. Ejemplos: {', '.join(ejemplos)}."
            )
        else:
            category_lines.append(f"- {categoria.nombre}: {categoria.total_productos} referencias.")

    featured_lines = [
        f"- {producto.nombre} ({producto.categoria.nombre if producto.categoria else 'Sin categoria'}) por {_format_cop(producto.precio)}."
        for producto in destacados
    ]

    return "\n".join(
        [
            "Marca: Casita de Regalos.",
            "Ubicacion: Bello, Antioquia. Cobertura: Medellin y area metropolitana.",
            "Estilo: cercano, premium, dulce, orientado a detalles personalizados.",
            "Flujo de compra: el cliente explora referencias, agrega al carrito y finaliza por WhatsApp para confirmar disponibilidad y pago.",
            "Pagos habituales: Nequi y Bancolombia. La confirmacion final se hace por WhatsApp.",
            "Politica comercial: personalizacion segun ocasion, presupuesto, colores y mensaje.",
            "Categorias activas:",
            category_lines and "\n".join(category_lines) or "- Sin categorias cargadas.",
            "Referencias destacadas del catalogo:",
            featured_lines and "\n".join(featured_lines) or "- Sin productos destacados disponibles.",
        ]
    )


def _build_system_prompt():
    return (
        "Eres la asesora virtual oficial de Casita de Regalos. "
        "Respondes en espanol natural, calido, claro y muy comercial, como una marca top actual. "
        "Tu objetivo es ayudar al cliente a elegir un detalle, resolver dudas y llevarlo con confianza a WhatsApp cuando ya quiera confirmar. "
        "No inventes productos inexistentes ni precios no vistos en el contexto. "
        "Si no estas completamente segura de algo, dilo con honestidad y sugiere confirmar por WhatsApp. "
        "Mantente breve: idealmente entre 45 y 110 palabras. "
        "Puedes recomendar categorias, tipos de regalo, ideas por presupuesto o por ocasion. "
        "Contexto real del negocio y catalogo:\n"
        f"{_serialize_catalog_context()}"
    )


def _sanitize_history(history):
    sanitized = []
    for item in history or []:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        text = str(item.get("text", "")).strip()
        if role not in {"user", "assistant"} or not text:
            continue
        sanitized.append({"role": role, "text": text[:900]})
    return sanitized[-8:]


def _extract_output_text(payload):
    output_text = str(payload.get("output_text", "")).strip()
    if output_text:
        return output_text

    fragments = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                fragments.append(text)

    return "\n".join(fragment.strip() for fragment in fragments if fragment.strip()).strip()


def _call_openai_responses_api(message, history):
    api_key = _get_openai_api_key()
    if not api_key:
        raise AssistantProviderError("OPENAI_API_KEY no esta configurada.")

    inputs = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": _build_system_prompt()}],
        }
    ]

    for item in _sanitize_history(history):
        inputs.append(
            {
                "role": item["role"],
                "content": [{"type": "input_text", "text": item["text"]}],
            }
        )

    inputs.append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": message.strip()}],
        }
    )

    payload = {
        "model": _get_openai_model(),
        "input": inputs,
        "max_output_tokens": 280,
    }

    raw_body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=raw_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AssistantProviderError(f"OpenAI respondio con error {exc.code}: {body[:240]}")
    except error.URLError as exc:
        raise AssistantProviderError(f"No se pudo conectar con OpenAI: {exc.reason}")

    text = _extract_output_text(data)
    if not text:
        raise AssistantProviderError("La respuesta del modelo llego vacia.")
    return text


def _build_actions(message):
    normalized = _normalize_text(message)
    categorias = list(Categoria.objects.order_by("nombre"))

    for categoria in categorias:
        if _normalize_text(categoria.nombre) in normalized:
            return [
                {
                    "label": f"Ver {categoria.nombre}",
                    "href": f"{reverse('inicio')}?categoria={categoria.id}#catalogo",
                },
                {
                    "label": "Hablar por WhatsApp",
                    "href": "https://wa.me/573116262155?text=Hola%20quiero%20cotizar%20un%20detalle",
                    "external": True,
                },
            ]

    if any(token in normalized for token in ["pago", "nequi", "bancolombia"]):
        return [
            {"label": "Ver como comprar", "href": f"{reverse('inicio')}#como-comprar"},
            {
                "label": "Pedir datos por WhatsApp",
                "href": "https://wa.me/573116262155?text=Hola%20quiero%20los%20datos%20de%20pago",
                "external": True,
            },
        ]

    if any(token in normalized for token in ["carrito", "agregar", "comprar"]):
        return [
            {"label": "Ir al carrito", "href": reverse("ver_carrito")},
            {"label": "Ver catalogo", "href": f"{reverse('inicio')}#catalogo"},
        ]

    return [
        {"label": "Ver catalogo", "href": f"{reverse('inicio')}#catalogo"},
        {
            "label": "WhatsApp",
            "href": "https://wa.me/573116262155?text=Hola%20quiero%20asesoria%20para%20elegir%20un%20detalle",
            "external": True,
        },
    ]


def _fallback_reply(message):
    normalized = _normalize_text(message)

    if any(token in normalized for token in ["tematico", "infantil", "personaje", "nino", "nina"]):
        text = (
            "Tenemos una linea tematica muy bonita con personajes, desayunos infantiles, cajas sorpresa y opciones personalizadas "
            "segun la edad, colores o presupuesto. Si me dices para quien es y cuanto quieres invertir, te oriento mejor."
        )
    elif any(token in normalized for token in ["amor", "aniversario", "romantico", "novia", "novio"]):
        text = (
            "Para algo romantico puedes mirar detalles con rosas, chocolates, corazones, cajas premium y desayunos sorpresa. "
            "Si quieres, te ayudo a elegir algo mas delicado, elegante o intenso segun la ocasion."
        )
    elif any(token in normalized for token in ["cumple", "desayuno", "sorpresa"]):
        text = (
            "La categoria de cumpleanos y desayunos tiene varias de las referencias mas fuertes de la marca. "
            "Hay cajas, bandejas, globos, frutas, snacks y presentaciones mas premium o mas express."
        )
    elif any(token in normalized for token in ["pago", "nequi", "bancolombia"]):
        text = (
            "La confirmacion final normalmente se coordina por WhatsApp despues de validar disponibilidad y personalizacion. "
            "Alli te comparten los datos de pago y el paso a paso del pedido."
        )
    else:
        text = (
            "Puedo ayudarte a elegir por ocasion, presupuesto, categoria o estilo de regalo. "
            "Tambien te puedo orientar sobre pagos, personalizacion o como finalizar por WhatsApp."
        )

    return {
        "message": text,
        "mode": "fallback",
        "configured": False,
        "actions": _build_actions(message),
    }


def get_assistant_reply(message, history=None):
    clean_message = (message or "").strip()
    if not clean_message:
        return {
            "message": "Escribeme algo y te ayudo a elegir un detalle lindo para esa ocasion.",
            "mode": "fallback",
            "configured": bool(_get_openai_api_key()),
            "actions": _build_actions("catalogo"),
        }

    if not _get_openai_api_key():
        return _fallback_reply(clean_message)

    try:
        ai_message = _call_openai_responses_api(clean_message, history or [])
    except AssistantProviderError:
        return _fallback_reply(clean_message)

    return {
        "message": ai_message,
        "mode": "ai",
        "configured": True,
        "actions": _build_actions(clean_message),
    }
