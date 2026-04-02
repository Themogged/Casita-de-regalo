from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def cop(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value

    entero = int(amount.quantize(Decimal("1")))
    return f"${entero:,}".replace(",", ".")
