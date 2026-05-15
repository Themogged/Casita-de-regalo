import json
import os
import unicodedata
from urllib import error, request

from django.core.cache import cache
from django.db.models import Count, Q
from django.urls import reverse

from .models import Categoria, Producto
from .whatsapp import DEFAULT_ASSISTANCE_MESSAGE, PAYMENT_DATA_MESSAGE, build_whatsapp_url


class AssistantProviderError(Exception):
    pass


def _normalize_text(value):
    normalized = unicodedata.normalize("NFD", str(value or ""))
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.strip().lower()


def _format_cop(value):
    return f"${int(value):,} COP".replace(",", ".")


def _get_openai_api_key():
    return os.getenv("OPENAI_API_KEY", "").strip()


def _get_openai_model():
    return os.getenv("OPENAI_ASSISTANT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def _serialize_catalog_context():
    cache_key = "assistant.catalog.context"
    cached_context = cache.get(cache_key)
    if cached_context:
        return cached_context

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
        f"- {producto.nombre} ({producto.categoria.nombre if producto.categoria else 'Sin categoría'}) por {_format_cop(producto.precio)}."
        for producto in destacados
    ]

    context = "\n".join(
        [
            "Marca: Casita de Regalos.",
            "Ubicación: Bello, Antioquia. Cobertura: Medellín y área metropolitana.",
            "Estilo: cercano, premium, delicado y orientado a detalles personalizados.",
            "Flujo de compra: el cliente explora referencias, guarda detalles para cotizar y finaliza por WhatsApp para confirmar disponibilidad y pago.",
            "Pagos habituales: Nequi y Bancolombia. La confirmación final se hace por WhatsApp.",
            "Política comercial: personalización según ocasión, presupuesto, colores y mensaje.",
            "Categorías activas:",
            category_lines and "\n".join(category_lines) or "- Sin categorías cargadas.",
            "Referencias destacadas del catálogo:",
            featured_lines and "\n".join(featured_lines) or "- Sin productos destacados disponibles.",
        ]
    )

    cache.set(cache_key, context, 300)
    return context


def _build_system_prompt():
    return (
        "Eres la asesora virtual oficial de Casita de Regalos. "
        "Respondes en español natural, cálido, claro y muy comercial. "
        "Tu objetivo es ayudar al cliente a elegir un detalle, resolver dudas y llevarlo con confianza a WhatsApp cuando ya quiera confirmar. "
        "No inventes productos inexistentes ni precios no vistos en el contexto. "
        "Si no estás completamente segura de algo, dilo con honestidad y sugiere confirmar por WhatsApp. "
        "Mantente breve: entre 45 y 110 palabras. "
        "Contexto real del negocio y catálogo:\n"
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


def _get_category_index():
    cache_key = "assistant.catalog.category_index"
    cached_index = cache.get(cache_key)
    if cached_index:
        return cached_index

    index = []
    for categoria in Categoria.objects.order_by("nombre"):
        normalized_name = _normalize_text(categoria.nombre)
        keywords = {normalized_name}
        for token in normalized_name.replace(" y ", " ").split():
            if len(token) >= 3:
                keywords.add(token)
        index.append(
            {
                "instance": categoria,
                "name": categoria.nombre,
                "normalized_name": normalized_name,
                "keywords": keywords,
            }
        )

    cache.set(cache_key, index, 300)
    return index


def _find_category_by_theme(normalized):
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
        for item in _get_category_index():
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

    numbers = []
    current = ""
    for char in normalized:
        if char.isdigit():
            current += char
        elif current:
            numbers.append(int(current))
            current = ""
    if current:
        numbers.append(int(current))

    if not numbers:
        return None

    amount = max(numbers)
    if amount < 1000:
        amount *= 1000

    margin = max(15000, int(amount * 0.25))
    return max(10000, amount - margin), amount + margin


def _detect_intent_and_context(message):
    normalized = _normalize_text(message)

    intents = []
    intent_map = {
        "saludo": ["hola", "buenas", "hey", "hello"],
        "presupuesto": ["precio", "costo", "cuanto", "valor", "presupuesto", "economico", "barato", "premium", "lujo", "caro"],
        "ocasion": ["cumple", "aniversario", "amor", "romantico", "amistad", "gracias", "sorpresa", "desayuno", "novia", "novio"],
        "infantil": ["nino", "nina", "infantil", "tematico", "tematicos", "personaje", "bebe"],
        "compra": ["comprar", "carrito", "agregar", "pedido", "adquirir", "finalizar"],
        "pago": ["pago", "pagos", "pagar", "nequi", "bancolombia", "transferencia", "consignar"],
        "entrega": ["entrega", "envio", "domicilio", "medellin", "bello", "direccion", "tiempo"],
        "personalizacion": ["personalizar", "personalizado", "mensaje", "nombre", "color", "tematica", "tema"],
        "consulta": ["catalogo", "productos", "referencias", "disponible", "opciones", "tienen", "muestran"],
        "contacto": ["whatsapp", "asesora", "asesoria", "contacto", "hablar"],
    }

    for intent, tokens in intent_map.items():
        if any(token in normalized for token in tokens):
            intents.append(intent)

    matched_category = None
    for item in _get_category_index():
        if item["normalized_name"] in normalized or any(keyword in normalized for keyword in item["keywords"]):
            matched_category = item["instance"]
            break

    if matched_category is None:
        matched_category = _find_category_by_theme(normalized)

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
    }
    search_tokens = [
        token for token in normalized.split()
        if len(token) >= 4 and token not in stopwords
    ]
    if search_tokens:
        product_query = Q()
        for token in search_tokens[:6]:
            product_query |= Q(nombre__icontains=token) | Q(descripcion__icontains=token)
        matched_products = list(
            Producto.objects.select_related("categoria")
            .filter(stock__gt=0)
            .filter(product_query)
            .order_by("-destacado", "precio", "nombre")[:3]
        )

    price_range = _detect_price_range(normalized)

    return {
        "normalized": normalized,
        "intents": intents,
        "category": matched_category,
        "products": matched_products,
        "price_range": price_range,
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


def _build_product_line(product):
    category_name = product.categoria.nombre if product.categoria else "catálogo general"
    return f"{product.nombre} en {category_name} por {_format_cop(product.precio)}"


def _build_fallback_actions(context_data):
    actions = []
    category = context_data["category"]
    intents = set(context_data["intents"])
    products = context_data["products"]

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
                "href": f"{reverse('inicio')}?categoria={category.id}#catalogo",
            }
        )

    if "compra" in intents:
        actions.append({"label": "Ir al carrito", "href": reverse("ver_carrito")})
    elif "pago" in intents or "entrega" in intents:
        actions.append({"label": "Cómo comprar", "href": f"{reverse('inicio')}#como-comprar"})
    elif not actions:
        actions.append({"label": "Ver catálogo", "href": f"{reverse('inicio')}#catalogo"})

    whatsapp_message = DEFAULT_ASSISTANCE_MESSAGE
    if products:
        whatsapp_message = f"Hola quiero cotizar {products[0].nombre}"
    elif category:
        whatsapp_message = f"Hola quiero cotizar algo de {category.nombre}"
    elif "pago" in intents:
        whatsapp_message = PAYMENT_DATA_MESSAGE
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
    products = context_data["products"] or _find_recommended_products(context_data)
    price_range = context_data["price_range"]

    greeting = "Hola, te ayudo a encontrar un detalle lindo y bien pensado."
    if "saludo" in intents and not intents - {"saludo"}:
        return (
            f"{greeting} Puedes preguntarme por categoría, presupuesto, pagos, personalización o entrega, "
            "y te guío rápido con opciones claras."
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
            "El tiempo exacto y el costo de entrega se confirman por WhatsApp según la zona y el tipo de detalle."
        )

    if "personalizacion" in intents:
        return (
            "Sí, se puede personalizar según ocasión, colores, mensaje, nombre o estilo del regalo. "
            "Lo ideal es elegir una base del catálogo y luego ajustar los detalles finos por WhatsApp."
        )

    if "compra" in intents:
        return (
            "Puedes explorar el catálogo, guardar detalles para cotizar y cerrar el pedido por WhatsApp. "
            "Así se confirma disponibilidad, personalización y pago sin perder tiempo."
        )

    if "consulta" in intents or category:
        if category:
            return (
                f"En {category.nombre} hay varias referencias activas y se pueden adaptar según presupuesto o estilo. "
                "Abre la categoría y desde ahí revisamos juntos la mejor opción."
            )
        return (
            "El catálogo está organizado por categorías para que encuentres rápido detalles románticos, infantiles, premium y opciones express. "
            "Si me dices la ocasión, te llevo más directo."
        )

    if "ocasion" in intents and price_range:
        return (
            f"Para esa ocasión se puede trabajar muy bien entre {_format_cop(price_range[0])} y {_format_cop(price_range[1])}. "
            "Si me dices si buscas algo romántico, infantil o premium, te aterrizo mejores referencias."
        )

    if "ocasion" in intents:
        return (
            "Tenemos detalles muy bonitos para cumpleaños, aniversarios, desayunos sorpresa y momentos especiales. "
            "Si me dices para quién es y cuánto quieres invertir, te recomiendo algo más preciso."
        )

    return (
        f"{greeting} Puedo orientarte por categoría, presupuesto, pagos, personalización o entrega, "
        "y después llevarte directo al catálogo o a WhatsApp para cerrar."
    )


def _fallback_reply(message):
    context_data = _detect_intent_and_context(message)
    return {
        "message": _build_fallback_message(context_data),
        "mode": "fallback",
        "configured": False,
        "actions": _build_fallback_actions(context_data),
    }


def get_assistant_reply(message, history=None):
    clean_message = (message or "").strip()
    if not clean_message:
        return {
            "message": "Escríbeme algo y te ayudo a elegir un detalle lindo, según ocasión, presupuesto o estilo.",
            "mode": "fallback",
            "configured": False,
            "actions": [
                {"label": "Ver catálogo", "href": f"{reverse('inicio')}#catalogo"},
                {"label": "Cómo comprar", "href": f"{reverse('inicio')}#como-comprar"},
                {
                    "label": "WhatsApp",
                    "href": build_whatsapp_url(DEFAULT_ASSISTANCE_MESSAGE),
                    "external": True,
                },
            ],
        }

    if _get_openai_api_key():
        try:
            context_data = _detect_intent_and_context(clean_message)
            ai_message = _call_openai_responses_api(clean_message, history or [])
            return {
                "message": ai_message,
                "mode": "ai",
                "configured": True,
                "actions": _build_fallback_actions(context_data),
            }
        except AssistantProviderError:
            pass

    return _fallback_reply(clean_message)
