from django import template

from productos.media_optimization import (
    optimized_image_url,
    responsive_image_srcset,
    webp_url,
)


register = template.Library()

register.filter("webp_url", webp_url)
register.filter("optimized_image_url", optimized_image_url)
register.filter("responsive_image_srcset", responsive_image_srcset)
