from decimal import Decimal
from urllib.parse import quote, urlparse

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from pedidos.models import Pedido, PedidoItem
from productos.models import Producto


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
    carrito = _normalize_carrito(request.session.get("carrito", {}))
    if carrito != request.session.get("carrito", {}):
        request.session["carrito"] = carrito
    return carrito


def _set_carrito(request, carrito):
    request.session["carrito"] = _normalize_carrito(carrito)
    request.session.modified = True


def _carrito_total_items(carrito):
    return sum(carrito.values())


def _es_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _build_whatsapp_url_for_pedido(pedido):
    lineas = [
        "*Pedido - Casita de Regalos*",
        "",
        f"Pedido #{pedido.id}",
    ]

    for item in pedido.items.all():
        lineas.append(
            f"- {item.producto_nombre} x{item.cantidad} = {_format_cop(item.subtotal())}"
        )

    lineas.extend(
        [
            "",
            f"Total: {_format_cop(pedido.total)}",
            "Quiero confirmar mi pedido",
        ]
    )

    mensaje = "\n".join(lineas)
    return f"https://wa.me/{settings.BUSINESS_WHATSAPP_NUMBER}?text={quote(mensaje)}"


def _redirect_despues_de_agregar(request):
    fallback = f"{reverse('inicio')}#catalogo"
    referer = request.META.get("HTTP_REFERER")

    if not referer:
        return redirect(fallback)

    parsed = urlparse(referer)

    if parsed.path == reverse("inicio"):
        limpio = referer.split("#", 1)[0]
        return redirect(f"{limpio}#catalogo")

    return redirect(referer)


@require_POST
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    carrito = _get_carrito(request)
    cantidad_actual = carrito.get(str(producto_id), 0)

    if cantidad_actual >= producto.stock:
        mensaje = f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}."
        if _es_ajax(request):
            return JsonResponse(
                {
                    "ok": False,
                    "level": "warning",
                    "message": mensaje,
                    "cart_total": _carrito_total_items(carrito),
                },
                status=400,
            )

        messages.warning(request, mensaje)
        return _redirect_despues_de_agregar(request)

    carrito[str(producto_id)] = cantidad_actual + 1
    _set_carrito(request, carrito)

    mensaje = f"{producto.nombre} agregado al carrito."

    if _es_ajax(request):
        return JsonResponse(
            {
                "ok": True,
                "level": "success",
                "message": mensaje,
                "cart_total": _carrito_total_items(carrito),
                "product_id": producto.id,
            }
        )

    messages.success(request, mensaje)
    return _redirect_despues_de_agregar(request)


@require_GET
def ver_carrito(request):
    carrito = _get_carrito(request)
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

    if carrito_actualizado != carrito:
        _set_carrito(request, carrito_actualizado)

    return render(
        request,
        "carrito.html",
        {
            "productos": productos,
            "total": total,
        },
    )


@require_POST
def sumar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito = _get_carrito(request)

    cantidad_actual = carrito.get(str(producto_id), 0)

    if cantidad_actual >= producto.stock:
        messages.warning(request, "Stock maximo alcanzado.")
        return redirect("ver_carrito")

    carrito[str(producto_id)] = cantidad_actual + 1
    _set_carrito(request, carrito)
    return redirect("ver_carrito")


@require_POST
def restar_producto(request, producto_id):
    carrito = _get_carrito(request)

    if str(producto_id) in carrito:
        carrito[str(producto_id)] -= 1
        if carrito[str(producto_id)] <= 0:
            del carrito[str(producto_id)]

    _set_carrito(request, carrito)
    return redirect("ver_carrito")


@require_POST
def eliminar_producto(request, producto_id):
    carrito = _get_carrito(request)

    if str(producto_id) in carrito:
        del carrito[str(producto_id)]

    _set_carrito(request, carrito)
    return redirect("ver_carrito")


@require_GET
def pedido_confirmado(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related("items"),
        id=pedido_id,
    )
    whatsapp_url = _build_whatsapp_url_for_pedido(pedido)

    return render(
        request,
        "pedido_confirmado.html",
        {
            "pedido": pedido,
            "whatsapp_url": whatsapp_url,
        },
    )


@require_POST
def enviar_carrito_whatsapp(request):
    carrito = _get_carrito(request)

    if not carrito:
        messages.warning(request, "Tu carrito esta vacio.")
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
                    messages.error(request, "Uno de los productos ya no esta disponible.")
                    return redirect("ver_carrito")

                if cantidad > producto.stock:
                    messages.warning(
                        request,
                        f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}. "
                        "Revisa tu carrito antes de continuar.",
                    )
                    return redirect("ver_carrito")

                subtotal = producto.precio * cantidad
                total += subtotal
                items_pedido.append((producto, cantidad, subtotal))

            pedido = Pedido.objects.create(total=total)

            for producto, cantidad, subtotal in items_pedido:
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto_nombre=producto.nombre,
                    cantidad=cantidad,
                    precio=producto.precio,
                )

                producto.stock -= cantidad
                producto.save(update_fields=["stock"])
    except ValueError:
        messages.error(request, "Hubo un problema con el carrito. Intenta nuevamente.")
        return redirect("ver_carrito")

    _set_carrito(request, {})
    request.session["ultimo_pedido_id"] = pedido.id
    messages.success(
        request,
        f"Pedido #{pedido.id} registrado. Revisa el resumen y confirma por WhatsApp.",
    )
    return redirect("pedido_confirmado", pedido_id=pedido.id)
