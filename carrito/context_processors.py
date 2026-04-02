def carrito_total(request):
    carrito = request.session.get('carrito', {})
    total = sum(carrito.values())
    return {'carrito_total': total}