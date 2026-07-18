import hashlib
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.urls import reverse

from productos.models import Producto

from .models import Carrito, CarritoItem


LEGACY_CART_SESSION_KEY = "carrito"
PERSISTENT_CART_SESSION_KEY = "persistent_cart_id"
PERSONALIZATION_FIELDS = (
    "texto_personalizado",
    "color",
    "variante",
    "fecha_entrega",
    "mensaje_regalo",
    "opciones",
    "imagen_hash",
)


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
            cart = Carrito.objects.filter(pk=stored_cart_id, usuario__isnull=True).first()
        if not cart:
            cart, _ = Carrito.objects.get_or_create(session_key=session_key)

    request.session[PERSISTENT_CART_SESSION_KEY] = cart.pk
    legacy = normalize_cart_mapping(request.session.get(LEGACY_CART_SESSION_KEY, {}))
    if legacy and not cart.items.exists():
        import_legacy_cart(cart, legacy)
    mirror_cart_to_session(request, cart)
    return cart


@transaction.atomic
def merge_carts(source, target):
    for source_item in source.items.select_related("producto"):
        target_item = (
            target.items.select_for_update()
            .filter(
                producto=source_item.producto,
                configuration_key=source_item.configuration_key,
            )
            .first()
        )
        if target_item:
            target_item.cantidad = min(
                target_item.producto.stock,
                target_item.cantidad + source_item.cantidad,
            )
            target_item.save(update_fields=["cantidad", "actualizado"])
            continue

        source_item.pk = None
        source_item.carrito = target
        source_item.save(force_insert=True)
    source.delete()
    return target


@transaction.atomic
def import_legacy_cart(cart, mapping):
    normalized = normalize_cart_mapping(mapping)
    product_ids = [int(product_id) for product_id in normalized]
    products = {product.pk: product for product in Producto.objects.filter(pk__in=product_ids)}
    for product_id, quantity in normalized.items():
        product = products.get(int(product_id))
        if not product:
            continue
        quantity = min(quantity, product.stock)
        if quantity <= 0:
            continue
        candidate = CarritoItem(carrito=cart, producto=product, cantidad=quantity)
        candidate.refresh_configuration_key()
        item, created = CarritoItem.objects.get_or_create(
            carrito=cart,
            producto=product,
            configuration_key=candidate.configuration_key,
            defaults={"cantidad": quantity},
        )
        if not created:
            item.cantidad = min(product.stock, item.cantidad + quantity)
            item.save(update_fields=["cantidad", "actualizado"])
    return cart


def mirror_cart_to_session(request, cart):
    mapping = {}
    for item in cart.items.only("producto_id", "cantidad"):
        if item.cantidad > 0:
            key = str(item.producto_id)
            mapping[key] = mapping.get(key, 0) + item.cantidad
    request.session[LEGACY_CART_SESSION_KEY] = mapping
    request.session[PERSISTENT_CART_SESSION_KEY] = cart.pk
    request.session.modified = True
    return mapping


def clear_cart(request, cart=None):
    cart = cart or get_cart_for_request(request)
    cart.items.all().delete()
    mirror_cart_to_session(request, cart)
    return cart


def _hash_upload(upload):
    digest = hashlib.sha256()
    position = upload.tell() if hasattr(upload, "tell") else 0
    for chunk in upload.chunks():
        digest.update(chunk)
    if hasattr(upload, "seek"):
        upload.seek(position)
    return digest.hexdigest()


def _extract_options(post_data):
    options = {}
    for key in post_data.keys():
        if not key.startswith(("opcion_", "extra_")):
            continue
        clean_key = key[:80]
        values = [str(value).strip()[:180] for value in post_data.getlist(key) if str(value).strip()]
        if values:
            options[clean_key] = values if len(values) > 1 else values[0]
    return options


def parse_personalization(post_data, uploaded_files=None, existing_item=None):
    uploaded_files = uploaded_files or {}
    fields = {
        "texto_personalizado": str(post_data.get("texto_personalizado", "")).strip()[:180],
        "color": str(post_data.get("color", "")).strip()[:80],
        "variante": str(post_data.get("variante", "")).strip()[:80],
        "mensaje_regalo": str(post_data.get("mensaje_regalo", "")).strip()[:500],
        "opciones": _extract_options(post_data),
    }

    delivery_date = str(post_data.get("fecha_entrega", "")).strip()
    fields["fecha_entrega"] = None
    if delivery_date:
        try:
            fields["fecha_entrega"] = date.fromisoformat(delivery_date)
        except ValueError as exc:
            raise ValidationError("Selecciona una fecha de entrega válida.") from exc
        if fields["fecha_entrega"] < date.today():
            raise ValidationError("La fecha de entrega no puede estar en el pasado.")

    image = uploaded_files.get("imagen_cliente")
    remove_image = str(post_data.get("eliminar_imagen", "")).lower() in {"1", "true", "on"}
    if image:
        fields["imagen_cliente"] = image
        fields["imagen_hash"] = _hash_upload(image)
    elif existing_item and not remove_image:
        fields["imagen_cliente"] = existing_item.imagen_cliente
        fields["imagen_hash"] = existing_item.imagen_hash
    else:
        fields["imagen_cliente"] = None
        fields["imagen_hash"] = ""
    return fields


def _configured_candidate(cart, product, fields, quantity=1):
    item = CarritoItem(carrito=cart, producto=product, cantidad=quantity, **fields)
    item.refresh_configuration_key()
    return item


@transaction.atomic
def add_configured_item(request, product, post_data, uploaded_files=None):
    cart = get_cart_for_request(request)
    product = Producto.objects.select_for_update().get(pk=product.pk)
    current_units = (
        cart.items.filter(producto=product).aggregate(total=Sum("cantidad"))["total"] or 0
    )
    if current_units >= product.stock:
        raise ValidationError(f"Solo hay {product.stock} unidades disponibles de {product.nombre}.")

    fields = parse_personalization(post_data, uploaded_files)
    candidate = _configured_candidate(cart, product, fields)
    item = (
        cart.items.select_for_update()
        .filter(producto=product, configuration_key=candidate.configuration_key)
        .first()
    )
    quantity_updated = item is not None
    if item:
        item.cantidad += 1
        item.save(update_fields=["cantidad", "actualizado"])
    else:
        candidate.full_clean()
        candidate.save()
        item = candidate

    mirror_cart_to_session(request, cart)
    return item, quantity_updated


@transaction.atomic
def update_item_personalization(item, post_data, uploaded_files=None):
    item = CarritoItem.objects.select_for_update().select_related("producto").get(pk=item.pk)
    fields = parse_personalization(post_data, uploaded_files, existing_item=item)
    candidate = _configured_candidate(item.carrito, item.producto, fields, item.cantidad)
    collision = (
        item.carrito.items.select_for_update()
        .filter(
            producto=item.producto,
            configuration_key=candidate.configuration_key,
        )
        .exclude(pk=item.pk)
        .first()
    )
    if collision:
        collision.cantidad += item.cantidad
        collision.save(update_fields=["cantidad", "actualizado"])
        item.delete()
        return collision

    for field, value in fields.items():
        setattr(item, field, value)
    item.configuration_key = candidate.configuration_key
    item.full_clean()
    item.save(
        update_fields=[
            "texto_personalizado",
            "color",
            "variante",
            "fecha_entrega",
            "mensaje_regalo",
            "opciones",
            "imagen_cliente",
            "imagen_hash",
            "configuration_key",
            "actualizado",
        ]
    )
    return item


def _format_cop(value):
    integer = int(Decimal(value).quantize(Decimal("1")))
    return f"${integer:,}".replace(",", ".")


def cart_snapshot(request, cart=None):
    cart = cart or get_cart_for_request(request)
    items = list(cart.items.select_related("producto", "producto__categoria"))
    total = sum((item.subtotal for item in items), Decimal("0.00"))
    units_by_product = {}
    for item in items:
        units_by_product[item.producto_id] = units_by_product.get(item.producto_id, 0) + item.cantidad

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
                "can_increase": units_by_product[product.pk] < product.stock,
                "subtotal_label": _format_cop(item.subtotal),
                "personalization": item.personalization_summary,
                "personalization_data": {
                    "text": item.texto_personalizado,
                    "color": item.color,
                    "variant": item.variante,
                    "delivery_date": item.fecha_entrega.isoformat() if item.fecha_entrega else "",
                    "gift_message": item.mensaje_regalo,
                    "options": item.opciones,
                    "customer_image_url": item.imagen_cliente.url if item.imagen_cliente else "",
                },
                "detail_url": reverse("detalle_producto", args=[product.pk]),
                "increase_url": reverse("sumar_item", args=[item.pk]),
                "decrease_url": reverse("restar_item", args=[item.pk]),
                "remove_url": reverse("eliminar_item", args=[item.pk]),
                "edit_url": reverse("editar_item_personalizacion", args=[item.pk]),
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
