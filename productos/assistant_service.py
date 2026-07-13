import json
import logging
import os
import re
import unicodedata
from urllib import error, request

from django.core.cache import cache
from django.db.models import Q
from django.urls import reverse

from .models import Categoria, Producto
from .whatsapp import DEFAULT_ASSISTANCE_MESSAGE, PAYMENT_DATA_MESSAGE, build_whatsapp_url


logger = logging.getLogger(__name__)


class AssistantProviderError(Exception):
    pass


def _normalize_text(value):
    normalized = unicodedata.normalize("NFD", str(value or ""))
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.strip().lower()


def _format_cop(value):
    return f"${int(value):,} COP".replace(",", ".")


ASSISTANT_SITE_GUIDE = "\n".join(
    [
        "- La lista para cotizar no es un pago inmediato: guarda referencias, cantidades y notas para confirmar por WhatsApp.",
        "- Arma tu regalo a medida ayuda a elegir ocasión, presupuesto, estilo, colores y una referencia inicial antes de cotizar.",
        "- Los precios publicados son valores base y pueden variar por personalización, disponibilidad, domicilio o acabados especiales.",
        "- Para cuidar los acabados conviene reservar con 1 a 2 días; los pedidos urgentes siempre se validan por WhatsApp.",
        "- La entrega se coordina según dirección, horario, cobertura y disponibilidad del día; no prometas tiempos ni costos sin confirmación.",
        "- Las fotografías son referencias reales de estilo; colores, flores, alimentos y decoración pueden ajustarse al pedido confirmado.",
        "- La web orienta y organiza la cotización, pero disponibilidad, valor final, pago y entrega se confirman con una asesora por WhatsApp.",
    ]
)

RECOMMENDATION_INTENTS = {"presupuesto", "ocasion", "infantil", "consulta", "recomendacion"}
CATEGORY_TOKEN_STOPWORDS = {
    "para",
    "con",
    "por",
    "los",
    "las",
    "del",
    "una",
    "uno",
    "regalo",
    "regalos",
    "detalle",
    "detalles",
}


def _get_openai_api_key():
    return os.getenv("OPENAI_API_KEY", "").strip()


def _get_openai_model():
    return os.getenv("OPENAI_ASSISTANT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def _serialize_catalog_context():
    cache_key = "assistant.catalog.context"
    cached_context = cache.get(cache_key)
    if cached_context:
        return cached_context

    active_products = list(
        Producto.objects.select_related("categoria")
        .filter(stock__gt=0)
        .order_by("-destacado", "precio", "nombre")
    )

    category_summary = {}
    for product in active_products:
        if not product.categoria:
            continue
        summary = category_summary.setdefault(
            product.categoria_id,
            {"name": product.categoria.nombre, "total": 0, "examples": []},
        )
        summary["total"] += 1
        if len(summary["examples"]) < 4:
            summary["examples"].append(product.nombre)

    category_lines = [
        f"- {summary['name']}: {summary['total']} referencias. Ejemplos: {', '.join(summary['examples'])}."
        for summary in sorted(category_summary.values(), key=lambda item: item["name"].casefold())
    ]

    featured_lines = [
        f"- {producto.nombre} ({producto.categoria.nombre if producto.categoria else 'Sin categoría'}) por {_format_cop(producto.precio)}."
        for producto in active_products[:14]
    ]

    context = "\n".join(
        [
            "Marca: Casita de Regalos.",
            "Ubicación: Bello, Antioquia. Cobertura: Medellín y área metropolitana.",
            "Estilo: cercano, cuidado, delicado y orientado a detalles personalizados.",
            "Flujo de compra: el cliente explora referencias, guarda detalles para cotizar y finaliza por WhatsApp para confirmar disponibilidad y pago.",
            "Pagos habituales: Nequi y Bancolombia. La confirmación final se hace por WhatsApp.",
            "Política comercial: personalización según ocasión, presupuesto, colores y mensaje.",
            "Guia operativa del sitio:",
            ASSISTANT_SITE_GUIDE,
            "Categorías activas:",
            category_lines and "\n".join(category_lines) or "- Sin categorías cargadas.",
            "Referencias destacadas del catálogo:",
            featured_lines and "\n".join(featured_lines) or "- Sin productos destacados disponibles.",
        ]
    )

    cache.set(cache_key, context, 300)
    return context


def _build_system_prompt(cart_context=""):
    session_context = f"\nContexto de la sesión actual:\n{cart_context}" if cart_context else ""
    return (
        "Eres la asesora virtual oficial de Casita de Regalos. "
        "Respondes en español natural, cálido, claro y muy comercial. "
        "Tu objetivo es ayudar al cliente a elegir un detalle, resolver dudas y llevarlo con confianza a WhatsApp cuando ya quiera confirmar. "
        "No inventes productos inexistentes ni precios no vistos en el contexto. "
        "Si no estás completamente segura de algo, dilo con honestidad y sugiere confirmar por WhatsApp. "
        "Si el cliente no sabe que escoger, pide ocasion, fecha y presupuesto aproximado. "
        "Evita sonar generica: usa el catalogo, la lista para cotizar y el regalo a medida como rutas concretas. "
        "Mantente breve: entre 45 y 110 palabras. "
        "Contexto real del negocio y catálogo:\n"
        f"{_serialize_catalog_context()}"
        f"{session_context}"
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


def _build_conversation_context(message, history):
    previous_user_turns = [
        item["text"]
        for item in _sanitize_history(history)
        if item["role"] == "user"
    ][-3:]
    return " ".join([*previous_user_turns, str(message or "").strip()]).strip()


def _summarize_cart(raw_cart):
    normalized_cart = {}
    for raw_product_id, raw_quantity in (raw_cart or {}).items():
        try:
            product_id = int(raw_product_id)
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            continue
        if product_id > 0 and quantity > 0:
            normalized_cart[product_id] = quantity

    if not normalized_cart:
        return {"references": 0, "units": 0, "items": []}

    products = {
        product.id: product
        for product in Producto.objects.filter(id__in=normalized_cart).only("id", "nombre", "precio")
    }
    items = []
    for product_id, quantity in normalized_cart.items():
        product = products.get(product_id)
        if not product:
            continue
        items.append(
            {
                "id": product.id,
                "name": product.nombre,
                "quantity": quantity,
                "price": product.precio,
            }
        )

    return {
        "references": len(items),
        "units": sum(item["quantity"] for item in items),
        "items": items,
    }


def _serialize_cart_context(cart_summary):
    if not cart_summary or not cart_summary["items"]:
        return "La lista para cotizar está vacía."

    item_lines = ", ".join(
        f'{item["name"]} x{item["quantity"]}'
        for item in cart_summary["items"][:5]
    )
    reference_label = "referencia" if cart_summary["references"] == 1 else "referencias"
    unit_label = "unidad" if cart_summary["units"] == 1 else "unidades"
    return (
        f'La lista para cotizar tiene {cart_summary["references"]} {reference_label} '
        f'y {cart_summary["units"]} {unit_label}: {item_lines}.'
    )


def _extract_output_text(payload):
    if not isinstance(payload, dict):
        return ""

    output_text = str(payload.get("output_text", "")).strip()
    if output_text:
        return output_text

    fragments = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if text:
                fragments.append(text)

    return "\n".join(fragment.strip() for fragment in fragments if fragment.strip()).strip()


def _call_openai_responses_api(message, history, cart_context=""):
    api_key = _get_openai_api_key()
    if not api_key:
        raise AssistantProviderError("OPENAI_API_KEY no está configurada.")

    inputs = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": _build_system_prompt(cart_context)}],
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
        with request.urlopen(req, timeout=20) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AssistantProviderError(f"OpenAI respondió con error {exc.code}: {body[:240]}")
    except error.URLError as exc:
        raise AssistantProviderError(f"No se pudo conectar con OpenAI: {exc.reason}")
    except TimeoutError:
        raise AssistantProviderError("La conexión con OpenAI superó el tiempo de espera.")

    try:
        data = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise AssistantProviderError("OpenAI devolvió una respuesta que no se pudo interpretar.") from exc

    text = _extract_output_text(data)
    if not text:
        raise AssistantProviderError("La respuesta del modelo llegó vacía.")
    return text


def _get_category_index():
    index = []
    for categoria in Categoria.objects.order_by("nombre"):
        normalized_name = _normalize_text(categoria.nombre)
        keywords = {normalized_name}
        for token in normalized_name.replace(" y ", " ").split():
            if len(token) >= 4 and token not in CATEGORY_TOKEN_STOPWORDS:
                keywords.add(token)
        index.append(
            {
                "instance": categoria,
                "name": categoria.nombre,
                "normalized_name": normalized_name,
                "keywords": keywords,
            }
        )

    return index


def _find_category_by_theme(normalized, category_index):
    theme_map = {
        "infantil": ["infantil", "tematic"],
        "romantico": ["amor", "anivers", "romantic"],
        "cumpleanos": ["cumple", "desayuno"],
        "premium": ["premium"],
        "mini": ["mini", "express"],
    }

    requested_themes = []
    if any(token in normalized for token in ["nino", "nina", "infantil", "tematico", "tematicos", "personaje", "bebe"]):
        requested_themes.append("infantil")
    if any(token in normalized for token in ["amor", "aniversario", "romantico", "novia", "novio"]):
        requested_themes.append("romantico")
    if any(token in normalized for token in ["cumple", "desayuno", "sorpresa"]):
        requested_themes.append("cumpleanos")
    if any(token in normalized for token in ["premium", "lujo"]):
        requested_themes.append("premium")
    if any(token in normalized for token in ["mini", "express"]):
        requested_themes.append("mini")

    for requested_theme in requested_themes:
        for item in category_index:
            if any(keyword in item["normalized_name"] for keyword in theme_map[requested_theme]):
                return item["instance"]
    return None


def _detect_price_range(normalized):
    explicit_map = {
        "economico": (20000, 50000),
        "barato": (20000, 45000),
        "bajo presupuesto": (20000, 45000),
        "medio": (50000, 85000),
        "moderado": (50000, 85000),
        "premium": (85000, 160000),
        "lujo": (120000, 260000),
        "caro": (90000, 220000),
    }

    for keyword, price_range in explicit_map.items():
        if keyword in normalized:
            return price_range

    raw_numbers = re.findall(r"\d[\d.,]*", normalized)
    numbers = []
    for raw_number in raw_numbers:
        digits = re.sub(r"\D", "", raw_number)
        if not digits:
            continue
        number = int(digits)
        if number < 1000 and any(marker in normalized for marker in [" mil", " k", "k "]):
            number *= 1000
        numbers.append(number)

    if not numbers:
        return None

    budget_markers = ["$", "cop", " mil", "presupuesto", "precio", "invertir", "tengo", "cuento con", "hasta"]
    if not any(marker in normalized for marker in budget_markers) and max(numbers) < 10000:
        return None

    if len(numbers) >= 2 and any(marker in normalized for marker in ["entre", "desde", "de "]):
        minimum, maximum = sorted(numbers[-2:])
        return max(10000, minimum), maximum

    amount = max(numbers)
    if amount < 1000:
        amount *= 1000

    if any(marker in normalized for marker in ["hasta", "maximo", "presupuesto", "tengo", "cuento con"]):
        return max(10000, int(amount * 0.55)), amount

    margin = max(12000, int(amount * 0.2))
    return max(10000, amount - margin), amount + margin


def _detect_intent_and_context(message, history=None, cart=None):
    normalized = _normalize_text(message)
    contextualized = _normalize_text(_build_conversation_context(message, history))

    intent_map = {
        "saludo": ["hola", "buenas", "hey", "hello"],
        "presupuesto": ["precio", "costo", "cuanto", "valor", "presupuesto", "economico", "barato", "premium", "lujo", "caro"],
        "ocasion": ["cumple", "aniversario", "amor", "romantico", "amistad", "gracias", "sorpresa", "desayuno", "novia", "novio"],
        "infantil": ["nino", "nina", "infantil", "tematico", "tematicos", "personaje", "bebe"],
        "compra": ["comprar", "carrito", "agregar", "pedido", "adquirir", "finalizar"],
        "lista": ["lista", "cotizar", "cotizacion", "resumen", "guardado", "guardados"],
        "pago": ["pago", "pagos", "pagar", "nequi", "bancolombia", "transferencia", "consignar"],
        "entrega": ["entrega", "envio", "domicilio", "medellin", "bello", "direccion", "tiempo"],
        "reserva": ["reserva", "reservar", "anticipacion", "urgente", "hoy", "manana"],
        "personalizacion": ["personalizar", "personalizado", "mensaje", "nombre", "color", "colores", "tematica", "tema"],
        "medida": ["medida", "armar", "arma", "crear", "disena", "diseñar", "modelo", "base"],
        "consulta": ["catalogo", "productos", "referencias", "disponible", "opciones", "tienen", "muestran"],
        "recomendacion": ["recomienda", "recomiendame", "elegir", "escojo", "escoger", "no se", "ayudame", "sugerencia"],
        "contacto": ["whatsapp", "asesora", "asesoria", "contacto", "hablar"],
    }

    current_intents = []
    contextual_intents = []
    for intent, tokens in intent_map.items():
        if any(token in normalized for token in tokens):
            current_intents.append(intent)
        if any(token in contextualized for token in tokens):
            contextual_intents.append(intent)

    category_index = _get_category_index()
    matched_category = None
    for item in category_index:
        if item["normalized_name"] in contextualized or any(keyword in contextualized for keyword in item["keywords"]):
            matched_category = item["instance"]
            break

    if matched_category is None:
        matched_category = _find_category_by_theme(contextualized, category_index)

    matched_products = []
    stopwords = {
        "quiero",
        "tengo",
        "algo",
        "para",
        "detalle",
        "regalo",
        "regalos",
        "una",
        "uno",
        "unos",
        "unas",
        "como",
        "puedo",
        "sobre",
        "del",
        "con",
        "por",
        "busco",
        "necesito",
        "fecha",
        "presupuesto",
        "ayuda",
        "ayudame",
        "elegir",
        "escojo",
        "escoger",
        "recomienda",
        "recomiendame",
    }
    search_tokens = [
        token for token in contextualized.split()
        if len(token) >= 4 and token not in stopwords
    ]
    product_search_intents = {
        "consulta",
        "recomendacion",
        "presupuesto",
        "ocasion",
        "infantil",
        "personalizacion",
        "medida",
    }
    should_search_products = not current_intents or bool(set(current_intents) & product_search_intents)
    if search_tokens and should_search_products:
        product_query = Q()
        for token in search_tokens[:6]:
            product_query |= Q(nombre__icontains=token) | Q(descripcion__icontains=token)
        matched_products = list(
            Producto.objects.select_related("categoria")
            .filter(stock__gt=0)
            .filter(product_query)
            .order_by("-destacado", "precio", "nombre")[:3]
        )

    current_price_range = _detect_price_range(normalized)
    price_range = current_price_range or _detect_price_range(contextualized)
    if current_price_range and "presupuesto" not in current_intents:
        current_intents.append("presupuesto")
    if price_range and "presupuesto" not in contextual_intents:
        contextual_intents.append("presupuesto")
    intents = current_intents or contextual_intents

    return {
        "normalized": normalized,
        "intents": intents,
        "current_intents": current_intents,
        "contextual_intents": contextual_intents,
        "category": matched_category,
        "products": matched_products,
        "price_range": price_range,
        "cart": _summarize_cart(cart),
    }


def _find_recommended_products(context_data, limit=3):
    query = Producto.objects.select_related("categoria").filter(stock__gt=0)
    category = context_data["category"]
    price_range = context_data["price_range"]
    intents = set(context_data["intents"])

    if category:
        query = query.filter(categoria=category)
    elif "infantil" in intents:
        query = query.filter(
            Q(categoria__nombre__icontains="infantil")
            | Q(categoria__nombre__icontains="tematic")
            | Q(nombre__icontains="infantil")
            | Q(nombre__icontains="tematic")
        )

    if price_range:
        min_price, max_price = price_range
        query = query.filter(precio__gte=min_price, precio__lte=max_price)

    products = list(query.order_by("-destacado", "precio", "nombre")[:limit])
    if products:
        return products

    if category:
        return list(
            Producto.objects.select_related("categoria")
            .filter(stock__gt=0, categoria=category)
            .order_by("-destacado", "precio", "nombre")[:limit]
        )

    return list(
        Producto.objects.select_related("categoria")
        .filter(stock__gt=0)
        .order_by("-destacado", "precio", "nombre")[:limit]
    )


def _get_context_products(context_data):
    if context_data["products"]:
        return context_data["products"]

    cached_products = context_data.get("recommended_products")
    if cached_products is not None:
        return cached_products

    intents = set(context_data["intents"])
    should_recommend = bool(
        intents & (RECOMMENDATION_INTENTS - {"recomendacion"})
        or context_data["category"]
        or context_data["price_range"]
    )
    products = _find_recommended_products(context_data) if should_recommend else []
    context_data["recommended_products"] = products
    return products


def _build_product_line(product):
    category_name = product.categoria.nombre if product.categoria else "catálogo general"
    return f"{product.nombre} en {category_name} por {_format_cop(product.precio)}"


def _build_fallback_actions(context_data):
    actions = []
    category = context_data["category"]
    intents = set(context_data["intents"])
    products = _get_context_products(context_data)

    if products:
        first_product = products[0]
        actions.append(
            {
                "label": f"Ver {first_product.nombre}",
                "href": reverse("detalle_producto", args=[first_product.id]),
            }
        )

    if category and not products:
        actions.append(
            {
                "label": f"Ver {category.nombre}",
                "href": f"{reverse('catalogo')}?categoria={category.id}#catalogo",
            }
        )

    if "medida" in intents or "personalizacion" in intents:
        actions.append({"label": "Armar regalo", "href": reverse("disena_regalo")})

    if "lista" in intents or "compra" in intents:
        actions.append({"label": "Ver mi lista", "href": reverse("ver_carrito")})
    elif "pago" in intents or "entrega" in intents:
        actions.append({"label": "Cómo comprar", "href": f"{reverse('inicio')}#como-comprar"})
    elif not actions:
        actions.append({"label": "Ver catálogo", "href": f"{reverse('catalogo')}#catalogo"})

    whatsapp_message = DEFAULT_ASSISTANCE_MESSAGE
    if products:
        whatsapp_message = f"Hola quiero cotizar {products[0].nombre}"
    elif category:
        whatsapp_message = f"Hola quiero cotizar algo de {category.nombre}"
    elif "pago" in intents:
        whatsapp_message = PAYMENT_DATA_MESSAGE
    elif "medida" in intents or "personalizacion" in intents:
        whatsapp_message = "Hola quiero armar un regalo a medida"
    elif "lista" in intents:
        whatsapp_message = "Hola quiero enviar mi lista para cotizar"
    elif "compra" in intents:
        whatsapp_message = "Hola quiero finalizar mi pedido"

    actions.append(
        {
            "label": "WhatsApp",
            "href": build_whatsapp_url(whatsapp_message),
            "external": True,
        }
    )

    unique = []
    seen = set()
    for action in actions:
        key = (action["label"], action.get("href"), action.get("prompt"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(action)
    return unique[:3]


def _build_fallback_message(context_data):
    intents = set(context_data["intents"])
    category = context_data["category"]
    products = _get_context_products(context_data)
    price_range = context_data["price_range"]
    cart_summary = context_data["cart"]

    greeting = "Hola, te ayudo a encontrar un detalle lindo y bien pensado."
    if "saludo" in intents and not intents - {"saludo"}:
        return (
            f"{greeting} Puedes preguntarme por categoría, presupuesto, pagos, personalización o entrega, "
            "y te guío rápido con opciones claras."
        )

    if "lista" in intents:
        if cart_summary["items"]:
            item_lines = ", ".join(
                f'{item["name"]} x{item["quantity"]}'
                for item in cart_summary["items"][:3]
            )
            reference_label = "referencia" if cart_summary["references"] == 1 else "referencias"
            unit_label = "unidad" if cart_summary["units"] == 1 else "unidades"
            return (
                f'Tu lista tiene {cart_summary["references"]} {reference_label} y {cart_summary["units"]} {unit_label}: {item_lines}. '
                "Todavía no es un pago; al enviarla por WhatsApp Casita confirma disponibilidad, personalización, entrega y valor final."
            )
        return (
            "Tu lista para cotizar está vacía. Puedes guardar referencias desde el catálogo sin pagar todavía y, cuando estés lista, "
            "enviarlas por WhatsApp para confirmar disponibilidad, personalización, entrega y valor final."
        )

    if "medida" in intents:
        return (
            "Para armar un regalo a medida, empieza por ocasión, presupuesto, estilo, colores y una referencia inicial. "
            "Con esa base Casita ajusta elementos, mensaje y acabados por WhatsApp antes de confirmar."
        )

    if "reserva" in intents:
        return (
            "Para cuidar mejor el armado, lo ideal es reservar con 1 a 2 días de anticipación. "
            "Si lo necesitas para hoy, conviene validar por WhatsApp disponibilidad, horario y tipo de detalle."
        )

    if "recomendacion" in intents and not ({"presupuesto", "ocasion", "infantil"} & intents) and not category:
        return (
            "Claro. Para recomendarte algo que sí encaje, dime tres datos: para quién es, la ocasión o fecha y cuánto quieres invertir. "
            "Con eso te muestro referencias reales del catálogo y la ruta más rápida para cotizar."
        )

    if products and category and "infantil" in intents:
        product_lines = "; ".join(_build_product_line(product) for product in products[:2])
        return (
            f"Para una línea temática e infantil te recomiendo empezar por {product_lines}. "
            "Si quieres, puedes abrir una referencia ahora mismo y luego cerrar la compra por WhatsApp."
        )

    if products and category:
        product_lines = "; ".join(_build_product_line(product) for product in products[:2])
        return (
            f"Para {category.nombre.lower()} te recomiendo empezar por {product_lines}. "
            "Si quieres, puedes abrir una referencia ahora mismo y luego cerrar la compra por WhatsApp."
        )

    if products and "presupuesto" in intents:
        product_lines = "; ".join(_build_product_line(product) for product in products[:2])
        return (
            f"Con ese presupuesto hay opciones que se ven muy bien, por ejemplo {product_lines}. "
            "Si me dices para quién es o la ocasión, te afino mejor la recomendación."
        )

    if "infantil" in intents:
        base_text = (
            "Para una línea temática e infantil tenemos propuestas con personajes, colores, desayunos y detalles personalizados. "
        )
        if products:
            sample = "; ".join(_build_product_line(product) for product in products[:2])
            return base_text + f"Ahora mismo puedes revisar {sample}. "
        return base_text + "Si me dices edad, personaje o presupuesto, te ubico mejor."

    if "pago" in intents:
        return (
            "El pago normalmente se confirma después de validar disponibilidad y personalización. "
            "Casita trabaja sobre todo con Nequi y Bancolombia, y el cierre final se hace por WhatsApp."
        )

    if "entrega" in intents:
        return (
            "La cobertura principal es Bello, Medellín y el área metropolitana. "
            "El horario, costo y disponibilidad de entrega se confirman por WhatsApp según la zona, fecha y tipo de detalle."
        )

    if "personalizacion" in intents:
        return (
            "Sí, puedes personalizar colores, mensaje, nombre, temática y estilo del regalo. "
            "Lo ideal es elegir una referencia del catálogo o usar el flujo a medida para llegar con una idea clara."
        )

    if "compra" in intents:
        return (
            "El flujo más claro es: ver catálogo, abrir la ficha del producto, agregar a la lista para cotizar y confirmar por WhatsApp. "
            "Así se valida disponibilidad, personalización, entrega y pago sin perder información."
        )

    if "consulta" in intents or category:
        if category:
            return (
                f"En {category.nombre} hay varias referencias activas y se pueden adaptar según presupuesto o estilo. "
                "Abre la categoría y desde ahí revisamos juntos la mejor opción."
            )
        return (
            "El catálogo está organizado por categorías para que encuentres rápido detalles románticos, infantiles, especiales y opciones express. "
            "Si me dices la ocasión, te llevo más directo."
        )

    if "ocasion" in intents and price_range:
        return (
            f"Para esa ocasión se puede trabajar muy bien entre {_format_cop(price_range[0])} y {_format_cop(price_range[1])}. "
            "Si me dices si buscas algo romántico, infantil o más elaborado, te aterrizo mejores referencias."
        )

    if "ocasion" in intents:
        return (
            "Tenemos detalles muy bonitos para cumpleaños, aniversarios, desayunos sorpresa y momentos especiales. "
            "Si me dices para quién es y cuánto quieres invertir, te recomiendo algo más preciso."
        )

    return (
        f"{greeting} Puedo orientarte por catálogo, lista para cotizar, regalo a medida, pagos, personalización o entrega. "
        "Dime para quién es, fecha y presupuesto aproximado para recomendarte mejor."
    )


def _fallback_reply(message, history=None, cart=None):
    context_data = _detect_intent_and_context(message, history=history, cart=cart)
    return {
        "message": _build_fallback_message(context_data),
        "mode": "fallback",
        "configured": False,
        "actions": _build_fallback_actions(context_data),
    }


def get_assistant_reply(message, history=None, cart=None):
    clean_message = (message or "").strip()
    if not clean_message:
        return {
            "message": "Escríbeme la ocasión, fecha o presupuesto y te ayudo a elegir catálogo, lista para cotizar o regalo a medida.",
            "mode": "fallback",
            "configured": False,
            "actions": [
                {"label": "Ver catálogo", "href": f"{reverse('catalogo')}#catalogo"},
                {"label": "Armar regalo", "href": reverse("disena_regalo")},
                {
                    "label": "WhatsApp",
                    "href": build_whatsapp_url(DEFAULT_ASSISTANCE_MESSAGE),
                    "external": True,
                },
            ],
        }

    context_data = _detect_intent_and_context(clean_message, history=history, cart=cart)
    cart_context = _serialize_cart_context(context_data["cart"])

    if _get_openai_api_key():
        try:
            ai_message = _call_openai_responses_api(clean_message, history or [], cart_context=cart_context)
            return {
                "message": ai_message,
                "mode": "ai",
                "configured": True,
                "actions": _build_fallback_actions(context_data),
            }
        except AssistantProviderError as exc:
            logger.warning("El proveedor del asistente falló; se usará la respuesta local: %s", exc)

    return {
        "message": _build_fallback_message(context_data),
        "mode": "fallback",
        "configured": False,
        "actions": _build_fallback_actions(context_data),
    }
