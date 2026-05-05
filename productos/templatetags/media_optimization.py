from pathlib import Path

from django import template
from django.conf import settings


register = template.Library()


@register.filter
def webp_url(url):
    if not url:
        return ''

    value = str(url)
    media_url = settings.MEDIA_URL
    if not value.startswith(media_url):
        return ''

    relative_path = value[len(media_url):].lstrip('/')
    if not relative_path:
        return ''

    media_root = Path(settings.MEDIA_ROOT).resolve()
    source_path = (media_root / relative_path).resolve()

    try:
        source_path.relative_to(media_root)
    except ValueError:
        return ''

    webp_path = source_path.with_suffix('.webp')
    if not webp_path.exists():
        return ''

    webp_relative_path = Path(relative_path).with_suffix('.webp').as_posix()
    return f'{media_url.rstrip("/")}/{webp_relative_path}'


@register.filter
def optimized_image_url(url):
    return webp_url(url) or url
