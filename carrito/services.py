from datetime import date
from decimal import Decimal

from django.db import transaction
from django.urls import reverse

from productos.models import Producto

from .models import Carrito, CarritoItem


LEGACY_CART_SESSION_KEY = "carrito"
PERSISTENT_CART_SESSION_KEY = "persistent_cart_id"


def normalize_cart_mapping(raw_cart):
    normalized = {}
    for product_id, quantity in (raw_cart or {}).items():
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if quantity > 0:
            normalized[str(product_id)] = quantity
    return normalized


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


@transaction.atomic
def get_cart_for_request(request):
    session_key = _ensure_session_key(request)
    stored_cart_id = request.session.get(PERSISTENT_CART_SESSION_KEY)

    if request.user.is_authenticated:
        cart, _ = Carrito.objects.select_for_update().get_or_create(usuario=request.user)
        anonymous_cart = None
        if stored_cart_id:
            anonymous_cart = (
                Carrito.objects.select_for_update()
                .filter(pk=stored_cart_id, usuario__isnull=True)
                .first()
            )
        if not anonymous_cart:
            anonymous_cart = (
                Carrito.objects.select_for_update()
                .filter(session_key=session_key, usuario__isnull=True)
                .first()
            )
        if anonymous_cart and anonymous_cart.pk != cart.pk:
            merge_carts(anonymous_cart, cart)
    else:
        cart = None
        if stored_cart_id:
            cart = Carrito.objects.filter(
                pk=stored_cart_id,
                usuario__isnull=True,
            ).first()
        if not cart:
            cart, _ = Carrito.objects.get_or_create(session_key=session_key)

    request.session[PERSISTENT_CART_SESSION_KEY] = cart.pk
    legacy = normalize_cart_mapping(request.session.get(LEGACY_CART_SESSION_KEY, {}))
    if legacy and not cart.items.exists():
        update_cart_from_mapping(cart, legacy)
    mirror_cart_to_session(request, cart)
    return cart


@transaction.atomic
def merge_carts(source, target):
    for source_item in source.items.select_related("producto"):
        target_item, created = CarritoItem.objects.get_or_create(
            carrito=target,
            producto=source_item.producto,
            defaults={
                "cantidad": source_item.cantidad,
                "texto_personalizado": source_item.texto_personalizado,
                "color": source_item.color,
                "variante": source_item.variante,
                "fecha_entrega": source_item.fecha_entrega,
                "mensaje_regalo": source_item.mensaje_regalo,
                "imagen_cliente": source_item.imagen_cliente,
            },
        )
        if not created:
            target_item.cantidad = min(
                target_item.producto.stock,
                target_item.cantidad + source_item.cantidad,
            )
            for field in (
                "texto_personalizado",
                "color",
                "variante",
                "fecha_entrega",
                "mensaje_regalo",
                "imagen_cliente",
            ):
                if not getattr(target_item, field) and getattr(source_item, field):
                    setattr(target_item, field, getattr(source_item, field))
            target_item.save()
    source.delete()
    return target


@transaction.atomic
def update_cart_from_mapping(cart, mapping):
    normalized = normalize_cart_mapping(mapping)
    product_ids = [int(product_id) for product_id in normalized]
    products = {product.pk: product for product in Producto.objects.filter(pk__in=product_ids)}
    cart.items.exclude(producto_id__in=product_ids).delete()
    for product_id, quantity in normalized.items():
        product = products.get(int(product_id))
        if not product:
            continue
        quantity = min(quantity, product.stock)
        if quantity <= 0:
            cart.items.filter(producto=product).delete()
            continue
        CarritoItem.objects.update_or_create(
            carrito=cart,
            producto=product,
            defaults={"cantidad": quantity},
        )
    return cart


def mirror_cart_to_session(request, cart):
    mapping = {
        str(item.producto_id): item.cantidad
        for item in cart.items.only("producto_id", "cantidad")
        if item.cantidad > 0
    }
    request.session[LEGACY_CART_SESSION_KEY] = mapping
    request.session[PERSISTENT_CART_SESSION_KEY] = cart.pk
    request.session.modified = True
    return mapping


def set_cart_mapping(request, mapping):
    cart = get_cart_for_request(request)
    update_cart_from_mapping(cart, mapping)
    return mirror_cart_to_session(request, cart)


def update_item_personalization(item, post_data, uploaded_files=None):
    uploaded_files = uploaded_files or {}
    fields = {
        "texto_personalizado": str(post_data.get("texto_personalizado", "")).strip()[:180],
        "color": str(post_data.get("color", "")).strip()[:80],
        "variante": str(post_data.get("variante", "")).strip()[:80],
        "mensaje_regalo": str(post_data.get("mensaje_regalo", "")).strip()[:500],
    }
    delivery_date = str(post_data.get("fecha_entrega", "")).strip()
    if delivery_date:
        try:
            fields["fecha_entrega"] = date.fromisoformat(delivery_date)
        except ValueError as exc:
            from django.core.exceptions import ValidationError

            raise ValidationError("Selecciona una fecha de entrega válida.") from exc
        if fields["fecha_entrega"] < date.today():
            from django.core.exceptions import ValidationError

            raise ValidationError("La fecha de entrega no puede estar en el pasado.")
    image = uploaded_files.get("imagen_cliente")
    changed = []
    for field, value in fields.items():
        if value not in ("", None) and getattr(item, field) != value:
            setattr(item, field, value)
            changed.append(field)
    if image:
        item.imagen_cliente = image
        changed.append("imagen_cliente")
    if changed:
        item.full_clean()
        item.save(update_fields=[*changed, "actualizado"])
    return item


def _format_cop(value):
    integer = int(Decimal(value).quantize(Decimal("1")))
    return f"${integer:,}".replace(",", ".")


def cart_snapshot(request, cart=None):
    cart = cart or get_cart_for_request(request)
    items = list(cart.items.select_related("producto", "producto__categoria"))
    total = sum((item.subtotal for item in items), Decimal("0.00"))
    serialized_items = []
    for item in items:
        product = item.producto
        serialized_items.append(
            {
                "id": item.pk,
                "product_id": product.pk,
                "name": product.nombre,
                "category": product.categoria.nombre if product.categoria else "Detalle",
                "image_url": product.imagen.url if product.imagen else "",
                "price_label": _format_cop(product.precio),
                "quantity": item.cantidad,
                "stock": product.stock,
                "subtotal_label": _format_cop(item.subtotal),
                "personalization": item.personalization_summary,
                "personalization_data": {
                    "text": item.texto_personalizado,
                    "color": item.color,
                    "variant": item.variante,
                    "delivery_date": item.fecha_entrega.isoformat() if item.fecha_entrega else "",
                    "gift_message": item.mensaje_regalo,
                    "customer_image_url": item.imagen_cliente.url if item.imagen_cliente else "",
                },
                "detail_url": reverse("detalle_producto", args=[product.pk]),
                "increase_url": reverse("sumar_producto", args=[product.pk]),
                "decrease_url": reverse("restar_producto", args=[product.pk]),
                "remove_url": reverse("eliminar_producto", args=[product.pk]),
            }
        )
    return {
        "items": serialized_items,
        "units": sum(item.cantidad for item in items),
        "references": len(items),
        "total_label": _format_cop(total),
        "is_empty": not items,
        "cart_url": reverse("ver_carrito"),
        "catalog_url": reverse("catalogo") + "#catalogo",
        "checkout_url": reverse("ver_carrito") + "#checkout-details-title",
    }
