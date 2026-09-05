from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .context_processors import CATEGORIES_MENU_CACHE_KEY
from .models import Categoria, Producto


@receiver([post_save, post_delete], sender=Categoria)
@receiver([post_save, post_delete], sender=Producto)
def clear_categories_menu_cache(sender, **kwargs):
    cache.delete(CATEGORIES_MENU_CACHE_KEY)
