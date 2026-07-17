from datetime import date
from decimal import Decimal
from urllib.parse import urlparse

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from pedidos.models import Pedido, PedidoItem
from productos.models import Producto
from productos.whatsapp import build_whatsapp_url

from .services import (
    cart_snapshot,
    get_cart_for_request,
    mirror_cart_to_session,
    set_cart_mapping,
    update_item_personalization,
)


def _format_cop(valor):
    entero = int(Decimal(valor).quantize(Decimal("1")))
    return f"${entero:,}".replace(",", ".")


def _normalize_carrito(raw_carrito):
    carrito = {}

    for producto_id, cantidad in (raw_carrito or {}).items():
        try:
            producto_id_int = int(producto_id)
            cantidad_int = int(cantidad)
        except (TypeError, ValueError):
            continue

        if cantidad_int > 0:
            carrito[str(producto_id_int)] = cantidad_int

    return carrito


def _get_carrito(request):
    cart = get_cart_for_request(request)
    return mirror_cart_to_session(request, cart)


def _set_carrito(request, carrito):
    set_cart_mapping(request, _normalize_carrito(carrito))


def _carrito_total_items(carrito):
    return sum(carrito.values())


def _build_cart_items(carrito):
    productos_ids = [int(producto_id) for producto_id in carrito.keys()]
    productos_map = {
        producto.id: producto for producto in Producto.objects.filter(id__in=productos_ids)
    }

    productos = []
    total = Decimal("0.00")
    carrito_actualizado = {}

    for producto_id, cantidad in carrito.items():
        producto = productos_map.get(int(producto_id))
        if not producto:
            continue

        subtotal = producto.precio * cantidad
        total += subtotal
        carrito_actualizado[str(producto.id)] = cantidad
        productos.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": subtotal,
            }
        )

    return productos, total, carrito_actualizado


def _es_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _json_cart_update(request, producto_id, message, level="success", status=200):
    persistent_cart = get_cart_for_request(request)
    carrito = mirror_cart_to_session(request, persistent_cart)
    productos, total, carrito_actualizado = _build_cart_items(carrito)

    if carrito_actualizado != carrito:
        _set_carrito(request, carrito_actualizado)
        carrito = carrito_actualizado

    item_actual = next(
        (
            item for item in productos
            if item["producto"].id == producto_id
        ),
        None,
    )

    payload = {
        "ok": status < 400,
        "level": level,
        "message": message,
        "product_id": producto_id,
        "cart_total": _carrito_total_items(carrito),
        "references_count": len(productos),
        "total_label": _format_cop(total),
        "cart_url": reverse("ver_carrito"),
        "is_empty": not productos,
        "item_removed": item_actual is None,
        "item_quantity": item_actual["cantidad"] if item_actual else 0,
        "item_subtotal_label": _format_cop(item_actual["subtotal"]) if item_actual else _format_cop(0),
        "item_stock": item_actual["producto"].stock if item_actual else 0,
        "cart": cart_snapshot(request),
    }
    return JsonResponse(payload, status=status)


def _json_checkout_error(message, status=400, redirect_url=None):
    payload = {
        "ok": False,
        "level": "warning",
        "message": message,
    }
    if redirect_url:
        payload["redirect_url"] = redirect_url
    return JsonResponse(payload, status=status)


def _build_whatsapp_url_for_pedido(pedido, checkout_data=None):
    lineas = [
        "*Pedido - Casita de Regalos*",
        "",
        f"Pedido #{pedido.id}",
    ]

    for item in pedido.items.all():
        lineas.append(
            f"- {item.producto_nombre} x{item.cantidad} = {_format_cop(item.subtotal())}"
        )
        if item.personalizacion:
            labels = {
                "texto_personalizado": "Texto",
                "color": "Color",
                "variante": "Tamaño o variante",
                "fecha_entrega": "Fecha",
                "mensaje_regalo": "Mensaje",
                "imagen_cliente": "Imagen",
            }
            for key, value in item.personalizacion.items():
                if value:
                    lineas.append(f"  · {labels.get(key, key)}: {value}")

    lineas.extend(
        [
            "",
            f"Total: {_format_cop(pedido.total)}",
        ]
    )

    checkout_data = checkout_data or {}
    detalle_personalizacion = [
        ("Ocasion", checkout_data.get("ocasion")),
        ("Para", checkout_data.get("para_quien")),
        ("Fecha de entrega", checkout_data.get("fecha_entrega")),
        ("Mensaje en tarjeta", checkout_data.get("mensaje_tarjeta")),
        ("Detalle adicional", checkout_data.get("detalle_extra")),
    ]

    datos_visibles = [(titulo, valor) for titulo, valor in detalle_personalizacion if valor]
    if datos_visibles:
        lineas.extend(["", "*Detalles para personalizar:*"])
        for titulo, valor in datos_visibles:
            lineas.append(f"- {titulo}: {valor}")

    lineas.extend(
        [
            "",
            "Quiero confirmar mi pedido y revisar disponibilidad final.",
        ]
    )

    return build_whatsapp_url("\n".join(lineas))


def _redirect_despues_de_agregar(request):
    fallback = f"{reverse('catalogo')}#catalogo"
    referer = request.META.get("HTTP_REFERER")

    if not referer:
        return redirect(fallback)

    parsed = urlparse(referer)

    if parsed.path == reverse("inicio"):
        limpio = referer.split("#", 1)[0]
        return redirect(f"{reverse('catalogo')}#catalogo")

    return redirect(referer)


@require_POST
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    # Create/load the session-backed cart before the transaction. Otherwise a
    # validation rollback can also remove a freshly created database session,
    # causing SessionMiddleware to raise SessionInterrupted on the response.
    carrito = _get_carrito(request)

    try:
        with transaction.atomic():
            cantidad_actual = carrito.get(str(producto_id), 0)
            cantidad_actualizada = cantidad_actual > 0

            if cantidad_actual >= producto.stock:
                mensaje = f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}."
                if _es_ajax(request):
                    return JsonResponse(
                        {
                            "ok": False,
                            "level": "warning",
                            "message": mensaje,
                            "cart_total": _carrito_total_items(carrito),
                            "cart": cart_snapshot(request),
                        },
                        status=400,
                    )

                messages.warning(request, mensaje)
                return _redirect_despues_de_agregar(request)

            carrito[str(producto_id)] = cantidad_actual + 1
            _set_carrito(request, carrito)
            persistent_cart = get_cart_for_request(request)
            persistent_item = persistent_cart.items.select_for_update().get(producto=producto)
            update_item_personalization(persistent_item, request.POST, request.FILES)
    except ValidationError as exc:
        persistent_cart.refresh_from_db()
        carrito = mirror_cart_to_session(request, persistent_cart)
        mensaje = exc.messages[0] if exc.messages else "Revisa los datos de personalización."
        if _es_ajax(request):
            return JsonResponse(
                {
                    "ok": False,
                    "level": "warning",
                    "message": mensaje,
                    "cart_total": _carrito_total_items(carrito),
                    "cart": cart_snapshot(request, persistent_cart),
                },
                status=400,
            )
        messages.warning(request, mensaje)
        return _redirect_despues_de_agregar(request)

    mensaje = (
        "Cantidad actualizada."
        if cantidad_actualizada
        else f"{producto.nombre} agregado a tu lista."
    )

    if _es_ajax(request):
        return JsonResponse(
            {
                "ok": True,
                "level": "success",
                "message": mensaje,
                "cart_total": _carrito_total_items(carrito),
                "product_id": producto.id,
                "product_name": producto.nombre,
                "product_image_url": producto.imagen.url if producto.imagen else "",
                "item_quantity": carrito.get(str(producto_id), 0),
                "quantity_updated": cantidad_actualizada,
                "cart": cart_snapshot(request),
            }
        )

    messages.success(request, mensaje)
    return _redirect_despues_de_agregar(request)


@require_GET
def ver_carrito(request):
    persistent_cart = get_cart_for_request(request)
    persistent_items = list(
        persistent_cart.items.select_related("producto", "producto__categoria")
    )
    productos = [
        {
            "producto": item.producto,
            "cantidad": item.cantidad,
            "subtotal": item.subtotal,
            "personalizacion": item.personalization_summary,
            "cart_item": item,
        }
        for item in persistent_items
    ]
    total = sum((item["subtotal"] for item in productos), Decimal("0.00"))
    mirror_cart_to_session(request, persistent_cart)

    return render(
        request,
        "carrito.html",
        {
            "productos": productos,
            "total": total,
            "checkout_prefill": request.session.get("checkout_prefill", {}),
            "cart_snapshot": cart_snapshot(request, persistent_cart),
        },
    )


@require_GET
def resumen_carrito(request):
    return JsonResponse({"ok": True, "cart": cart_snapshot(request)})


@require_POST
def sumar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito = _get_carrito(request)

    cantidad_actual = carrito.get(str(producto_id), 0)

    if cantidad_actual >= producto.stock:
        mensaje = "Stock maximo alcanzado."
        if _es_ajax(request):
            return _json_cart_update(
                request,
                producto.id,
                mensaje,
                level="warning",
                status=400,
            )
        messages.warning(request, mensaje)
        return redirect("ver_carrito")

    carrito[str(producto_id)] = cantidad_actual + 1
    _set_carrito(request, carrito)
    if _es_ajax(request):
        return _json_cart_update(request, producto.id, "Cantidad actualizada.")
    return redirect("ver_carrito")


@require_POST
def restar_producto(request, producto_id):
    carrito = _get_carrito(request)

    if str(producto_id) in carrito:
        carrito[str(producto_id)] -= 1
        if carrito[str(producto_id)] <= 0:
            del carrito[str(producto_id)]

    _set_carrito(request, carrito)
    if _es_ajax(request):
        return _json_cart_update(request, producto_id, "Cantidad actualizada.")
    return redirect("ver_carrito")


@require_POST
def eliminar_producto(request, producto_id):
    carrito = _get_carrito(request)

    if str(producto_id) in carrito:
        del carrito[str(producto_id)]

    _set_carrito(request, carrito)
    if _es_ajax(request):
        return _json_cart_update(request, producto_id, "Producto retirado de la lista.")
    return redirect("ver_carrito")


@require_POST
def enviar_carrito_whatsapp(request):
    carrito = _get_carrito(request)
    persistent_cart = get_cart_for_request(request)
    persistent_items = {
        item.producto_id: item
        for item in persistent_cart.items.select_related("producto")
    }
    checkout_data = {
        "ocasion": request.POST.get("ocasion", "").strip(),
        "para_quien": request.POST.get("para_quien", "").strip(),
        "fecha_entrega": request.POST.get("fecha_entrega", "").strip(),
        "mensaje_tarjeta": request.POST.get("mensaje_tarjeta", "").strip(),
        "detalle_extra": request.POST.get("detalle_extra", "").strip(),
    }
    request.session["checkout_prefill"] = checkout_data
    request.session.modified = True

    if not carrito:
        mensaje = "Aún no has guardado detalles para cotizar."
        if _es_ajax(request):
            return _json_checkout_error(mensaje, redirect_url=reverse("ver_carrito"))
        messages.warning(request, mensaje)
        return redirect("ver_carrito")

    missing_fields = []
    if not checkout_data["para_quien"]:
        missing_fields.append("para quién es")
    if not checkout_data["fecha_entrega"]:
        missing_fields.append("fecha de entrega")
    if missing_fields:
        mensaje = "Completa " + " y ".join(missing_fields) + " antes de continuar."
        if _es_ajax(request):
            return _json_checkout_error(mensaje, status=400, redirect_url=reverse("ver_carrito"))
        messages.warning(request, mensaje)
        return redirect("ver_carrito")

    try:
        delivery_date = date.fromisoformat(checkout_data["fecha_entrega"])
    except ValueError:
        mensaje = "Selecciona una fecha de entrega válida."
        if _es_ajax(request):
            return _json_checkout_error(mensaje, status=400, redirect_url=reverse("ver_carrito"))
        messages.warning(request, mensaje)
        return redirect("ver_carrito")
    if delivery_date < date.today():
        mensaje = "La fecha de entrega no puede estar en el pasado."
        if _es_ajax(request):
            return _json_checkout_error(mensaje, status=400, redirect_url=reverse("ver_carrito"))
        messages.warning(request, mensaje)
        return redirect("ver_carrito")

    total = Decimal("0.00")
    items_pedido = []

    try:
        with transaction.atomic():
            productos_ids = [int(producto_id) for producto_id in carrito.keys()]
            productos = {
                producto.id: producto
                for producto in Producto.objects.select_for_update().filter(id__in=productos_ids)
            }

            for producto_id, cantidad in carrito.items():
                producto = productos.get(int(producto_id))

                if not producto:
                    mensaje = "Uno de los productos ya no está disponible."
                    if _es_ajax(request):
                        return _json_checkout_error(mensaje, redirect_url=reverse("ver_carrito"))
                    messages.error(request, mensaje)
                    return redirect("ver_carrito")

                if cantidad > producto.stock:
                    mensaje = (
                        f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}. "
                        "Revisa tu carrito antes de continuar."
                    )
                    if _es_ajax(request):
                        return _json_checkout_error(mensaje, redirect_url=reverse("ver_carrito"))
                    messages.warning(request, mensaje)
                    return redirect("ver_carrito")

                subtotal = producto.precio * cantidad
                total += subtotal
                cart_item = persistent_items.get(producto.id)
                personalization = {}
                if cart_item:
                    personalization = {
                        "texto_personalizado": cart_item.texto_personalizado,
                        "color": cart_item.color,
                        "variante": cart_item.variante,
                        "fecha_entrega": cart_item.fecha_entrega.isoformat() if cart_item.fecha_entrega else "",
                        "mensaje_regalo": cart_item.mensaje_regalo,
                        "imagen_cliente": cart_item.imagen_cliente.url if cart_item.imagen_cliente else "",
                    }
                items_pedido.append((producto, cantidad, subtotal, personalization))

            pedido = Pedido.objects.create(
                total=total,
                usuario=request.user if request.user.is_authenticated else None,
                fecha_entrega=delivery_date,
                detalles_personalizacion=checkout_data,
            )

            for producto, cantidad, subtotal, personalization in items_pedido:
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto_nombre=producto.nombre,
                    cantidad=cantidad,
                    precio=producto.precio,
                    personalizacion=personalization,
                )

                producto.stock -= cantidad
                producto.save(update_fields=["stock"])
    except ValueError:
        mensaje = "Hubo un problema con el carrito. Intenta nuevamente."
        if _es_ajax(request):
            return _json_checkout_error(mensaje, status=500, redirect_url=reverse("ver_carrito"))
        messages.error(request, mensaje)
        return redirect("ver_carrito")

    _set_carrito(request, {})
    request.session.pop("checkout_prefill", None)
    request.session.modified = True
    whatsapp_url = _build_whatsapp_url_for_pedido(pedido, checkout_data=checkout_data)

    if _es_ajax(request):
        return JsonResponse(
            {
                "ok": True,
                "level": "success",
                "message": "Abriendo WhatsApp con tu pedido...",
                "whatsapp_url": whatsapp_url,
                "cart_total": 0,
                "order_id": pedido.id,
            }
        )

    return redirect(whatsapp_url)
