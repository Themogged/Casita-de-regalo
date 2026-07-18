from datetime import date
from decimal import Decimal
from urllib.parse import urlparse

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from pedidos.models import Pedido, PedidoItem
from productos.models import Producto
from productos.whatsapp import build_whatsapp_url

from .models import CarritoItem
from .services import (
    add_configured_item,
    cart_snapshot,
    clear_cart,
    get_cart_for_request,
    mirror_cart_to_session,
    update_item_personalization,
)


def _format_cop(value):
    integer = int(Decimal(value).quantize(Decimal("1")))
    return f"${integer:,}".replace(",", ".")


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _cart_item_for_request(request, item_id):
    cart = get_cart_for_request(request)
    return get_object_or_404(
        cart.items.select_related("producto", "producto__categoria"),
        pk=item_id,
    )


def _json_cart_update(request, item_id, message, level="success", status=200, product_id=None):
    cart = get_cart_for_request(request)
    snapshot = cart_snapshot(request, cart)
    current = next((item for item in snapshot["items"] if item["id"] == item_id), None)
    payload = {
        "ok": status < 400,
        "level": level,
        "message": message,
        "item_id": item_id,
        "product_id": product_id or (current["product_id"] if current else None),
        "cart_total": snapshot["units"],
        "references_count": snapshot["references"],
        "total_label": snapshot["total_label"],
        "cart_url": snapshot["cart_url"],
        "is_empty": snapshot["is_empty"],
        "item_removed": current is None,
        "item_quantity": current["quantity"] if current else 0,
        "item_subtotal_label": current["subtotal_label"] if current else _format_cop(0),
        "item_stock": current["stock"] if current else 0,
        "cart": snapshot,
    }
    return JsonResponse(payload, status=status)


def _json_checkout_error(message, status=400, redirect_url=None):
    payload = {"ok": False, "level": "warning", "message": message}
    if redirect_url:
        payload["redirect_url"] = redirect_url
    return JsonResponse(payload, status=status)


def _build_whatsapp_url_for_order(order, checkout_data=None):
    lines = ["*Pedido - Casita de Regalos*", "", f"Pedido #{order.id}"]
    labels = {
        "texto_personalizado": "Texto",
        "color": "Color",
        "variante": "Tamaño o variante",
        "fecha_entrega": "Fecha",
        "mensaje_regalo": "Mensaje",
        "imagen_cliente": "Imagen",
        "opciones": "Opciones",
    }
    for item in order.items.all():
        lines.append(f"- {item.producto_nombre} x{item.cantidad} = {_format_cop(item.subtotal())}")
        for key, value in (item.personalizacion or {}).items():
            if value:
                lines.append(f"  · {labels.get(key, key)}: {value}")

    lines.extend(["", f"Total: {_format_cop(order.total)}"])
    checkout_data = checkout_data or {}
    details = [
        ("Ocasión", checkout_data.get("ocasion")),
        ("Para", checkout_data.get("para_quien")),
        ("Fecha de entrega", checkout_data.get("fecha_entrega")),
        ("Mensaje en tarjeta", checkout_data.get("mensaje_tarjeta")),
        ("Detalle adicional", checkout_data.get("detalle_extra")),
    ]
    visible_details = [(title, value) for title, value in details if value]
    if visible_details:
        lines.extend(["", "*Detalles para personalizar:*"])
        lines.extend(f"- {title}: {value}" for title, value in visible_details)
    lines.extend(["", "Quiero confirmar mi pedido y revisar disponibilidad final."])
    return build_whatsapp_url("\n".join(lines))


def _redirect_after_add(request):
    fallback = f"{reverse('catalogo')}#catalogo"
    referer = request.META.get("HTTP_REFERER")
    if not referer:
        return redirect(fallback)
    parsed = urlparse(referer)
    if parsed.path == reverse("inicio"):
        return redirect(fallback)
    return redirect(referer)


@require_POST
def agregar_al_carrito(request, producto_id):
    product = get_object_or_404(Producto, id=producto_id)
    # Persist the session/cart before the validation transaction so an invalid
    # personalization cannot roll back the database-backed session itself.
    get_cart_for_request(request)
    try:
        item, quantity_updated = add_configured_item(request, product, request.POST, request.FILES)
    except ValidationError as exc:
        message = exc.messages[0] if exc.messages else "Revisa los datos de personalización."
        if _is_ajax(request):
            snapshot = cart_snapshot(request)
            return JsonResponse(
                {
                    "ok": False,
                    "level": "warning",
                    "message": message,
                    "cart_total": snapshot["units"],
                    "cart": snapshot,
                },
                status=400,
            )
        messages.warning(request, message)
        return _redirect_after_add(request)

    message = "Cantidad actualizada." if quantity_updated else f"{product.nombre} agregado a tu lista."
    if _is_ajax(request):
        snapshot = cart_snapshot(request)
        return JsonResponse(
            {
                "ok": True,
                "level": "success",
                "message": message,
                "cart_total": snapshot["units"],
                "product_id": product.id,
                "item_id": item.id,
                "product_name": product.nombre,
                "product_image_url": product.imagen.url if product.imagen else "",
                "item_quantity": item.cantidad,
                "quantity_updated": quantity_updated,
                "cart": snapshot,
            }
        )
    messages.success(request, message)
    return _redirect_after_add(request)


@require_GET
def ver_carrito(request):
    cart = get_cart_for_request(request)
    persistent_items = list(cart.items.select_related("producto", "producto__categoria"))
    units_by_product = {}
    for item in persistent_items:
        units_by_product[item.producto_id] = units_by_product.get(item.producto_id, 0) + item.cantidad
    products = [
        {
            "producto": item.producto,
            "cantidad": item.cantidad,
            "subtotal": item.subtotal,
            "personalizacion": item.personalization_summary,
            "cart_item": item,
            "can_increase": units_by_product[item.producto_id] < item.producto.stock,
        }
        for item in persistent_items
    ]
    total = sum((item["subtotal"] for item in products), Decimal("0.00"))
    mirror_cart_to_session(request, cart)
    return render(
        request,
        "carrito.html",
        {
            "productos": products,
            "total": total,
            "checkout_prefill": request.session.get("checkout_prefill", {}),
            "cart_snapshot": cart_snapshot(request, cart),
        },
    )


@require_GET
def resumen_carrito(request):
    return JsonResponse({"ok": True, "cart": cart_snapshot(request)})


def _change_item_quantity(request, item, delta):
    product_id = item.producto_id
    cart = item.carrito
    if delta > 0:
        product_units = cart.items.filter(producto_id=product_id).aggregate(total=Sum("cantidad"))["total"] or 0
        if product_units >= item.producto.stock:
            message = "Stock máximo alcanzado."
            if _is_ajax(request):
                return _json_cart_update(
                    request, item.id, message, level="warning", status=400, product_id=product_id
                )
            messages.warning(request, message)
            return redirect("ver_carrito")

    item.cantidad += delta
    item_id = item.id
    if item.cantidad <= 0:
        item.delete()
    else:
        item.save(update_fields=["cantidad", "actualizado"])
    mirror_cart_to_session(request, cart)
    if _is_ajax(request):
        return _json_cart_update(request, item_id, "Cantidad actualizada.", product_id=product_id)
    return redirect("ver_carrito")


@require_POST
def sumar_item(request, item_id):
    return _change_item_quantity(request, _cart_item_for_request(request, item_id), 1)


@require_POST
def restar_item(request, item_id):
    return _change_item_quantity(request, _cart_item_for_request(request, item_id), -1)


@require_POST
def eliminar_item(request, item_id):
    item = _cart_item_for_request(request, item_id)
    product_id = item.producto_id
    cart = item.carrito
    item.delete()
    mirror_cart_to_session(request, cart)
    if _is_ajax(request):
        return _json_cart_update(
            request,
            item_id,
            "Producto retirado de la lista.",
            product_id=product_id,
        )
    messages.success(request, "Producto retirado de la lista.")
    return redirect("ver_carrito")


@require_POST
def editar_item_personalizacion(request, item_id):
    item = _cart_item_for_request(request, item_id)
    try:
        updated_item = update_item_personalization(item, request.POST, request.FILES)
    except ValidationError as exc:
        message = exc.messages[0] if exc.messages else "Revisa los datos de personalización."
        if _is_ajax(request):
            return _json_cart_update(request, item.id, message, level="warning", status=400)
        messages.warning(request, message)
        return redirect(f"{reverse('ver_carrito')}#item-{item.id}")

    mirror_cart_to_session(request, updated_item.carrito)
    if _is_ajax(request):
        return _json_cart_update(request, updated_item.id, "Personalización actualizada.")
    messages.success(request, "Personalización actualizada.")
    return redirect(f"{reverse('ver_carrito')}#item-{updated_item.id}")


def _legacy_item(request, product_id):
    cart = get_cart_for_request(request)
    item = (
        cart.items.select_related("producto", "producto__categoria")
        .filter(producto_id=product_id)
        .order_by("id")
        .first()
    )
    if item is None:
        raise Http404("La referencia no está en la lista.")
    return item


@require_POST
def sumar_producto(request, producto_id):
    return _change_item_quantity(request, _legacy_item(request, producto_id), 1)


@require_POST
def restar_producto(request, producto_id):
    return _change_item_quantity(request, _legacy_item(request, producto_id), -1)


@require_POST
def eliminar_producto(request, producto_id):
    item = _legacy_item(request, producto_id)
    return eliminar_item(request, item.id)


@require_POST
def enviar_carrito_whatsapp(request):
    cart = get_cart_for_request(request)
    cart_items = list(cart.items.select_related("producto"))
    checkout_data = {
        "ocasion": request.POST.get("ocasion", "").strip(),
        "para_quien": request.POST.get("para_quien", "").strip(),
        "fecha_entrega": request.POST.get("fecha_entrega", "").strip(),
        "mensaje_tarjeta": request.POST.get("mensaje_tarjeta", "").strip(),
        "detalle_extra": request.POST.get("detalle_extra", "").strip(),
    }
    request.session["checkout_prefill"] = checkout_data
    request.session.modified = True

    if not cart_items:
        message = "Aún no has guardado detalles para cotizar."
        if _is_ajax(request):
            return _json_checkout_error(message, redirect_url=reverse("ver_carrito"))
        messages.warning(request, message)
        return redirect("ver_carrito")

    missing_fields = []
    if not checkout_data["para_quien"]:
        missing_fields.append("para quién es")
    if not checkout_data["fecha_entrega"]:
        missing_fields.append("fecha de entrega")
    if missing_fields:
        message = "Completa " + " y ".join(missing_fields) + " antes de continuar."
        if _is_ajax(request):
            return _json_checkout_error(message, redirect_url=reverse("ver_carrito"))
        messages.warning(request, message)
        return redirect("ver_carrito")

    try:
        delivery_date = date.fromisoformat(checkout_data["fecha_entrega"])
    except ValueError:
        message = "Selecciona una fecha de entrega válida."
        if _is_ajax(request):
            return _json_checkout_error(message, redirect_url=reverse("ver_carrito"))
        messages.warning(request, message)
        return redirect("ver_carrito")
    if delivery_date < date.today():
        message = "La fecha de entrega no puede estar en el pasado."
        if _is_ajax(request):
            return _json_checkout_error(message, redirect_url=reverse("ver_carrito"))
        messages.warning(request, message)
        return redirect("ver_carrito")

    try:
        with transaction.atomic():
            product_ids = {item.producto_id for item in cart_items}
            locked_products = {
                product.id: product
                for product in Producto.objects.select_for_update().filter(id__in=product_ids)
            }
            units_by_product = {}
            for item in cart_items:
                units_by_product[item.producto_id] = units_by_product.get(item.producto_id, 0) + item.cantidad
            for product_id, quantity in units_by_product.items():
                product = locked_products.get(product_id)
                if not product:
                    raise ValidationError("Uno de los productos ya no está disponible.")
                if quantity > product.stock:
                    raise ValidationError(
                        f"Solo hay {product.stock} unidades disponibles de {product.nombre}."
                    )

            total = sum((item.subtotal for item in cart_items), Decimal("0.00"))
            order = Pedido.objects.create(
                total=total,
                usuario=request.user if request.user.is_authenticated else None,
                fecha_entrega=delivery_date,
                detalles_personalizacion=checkout_data,
            )
            for item in cart_items:
                personalization = {
                    "texto_personalizado": item.texto_personalizado,
                    "color": item.color,
                    "variante": item.variante,
                    "fecha_entrega": item.fecha_entrega.isoformat() if item.fecha_entrega else "",
                    "mensaje_regalo": item.mensaje_regalo,
                    "imagen_cliente": item.imagen_cliente.url if item.imagen_cliente else "",
                    "opciones": item.opciones,
                }
                PedidoItem.objects.create(
                    pedido=order,
                    producto_nombre=item.producto.nombre,
                    cantidad=item.cantidad,
                    precio=item.producto.precio,
                    personalizacion=personalization,
                )
            for product_id, quantity in units_by_product.items():
                product = locked_products[product_id]
                product.stock -= quantity
                product.save(update_fields=["stock"])
    except ValidationError as exc:
        message = exc.messages[0]
        if _is_ajax(request):
            return _json_checkout_error(message, redirect_url=reverse("ver_carrito"))
        messages.warning(request, message)
        return redirect("ver_carrito")

    clear_cart(request, cart)
    request.session.pop("checkout_prefill", None)
    request.session.modified = True
    whatsapp_url = _build_whatsapp_url_for_order(order, checkout_data)
    if _is_ajax(request):
        return JsonResponse(
            {
                "ok": True,
                "level": "success",
                "message": "Abriendo WhatsApp con tu pedido...",
                "whatsapp_url": whatsapp_url,
                "cart_total": 0,
                "order_id": order.id,
            }
        )
    return redirect(whatsapp_url)
