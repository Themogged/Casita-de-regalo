from django.db import DatabaseError
from django.db.models import Count

from .models import AssistantProfile


def assistant_account_context(request):
    context = {
        "assistant_memory_enabled": False,
        "assistant_memory_active": False,
        "assistant_memory_count": 0,
    }
    if not request.user.is_authenticated:
        return context
    try:
        profile = (
            AssistantProfile.objects.filter(user_id=request.user.pk)
            .annotate(memory_count=Count("user__assistant_memories"))
            .only("memory_enabled", "memory_paused_until")
            .first()
        )
        if profile is None:
            return context
        context.update(
            {
                "assistant_memory_enabled": profile.memory_enabled,
                "assistant_memory_active": profile.is_memory_active,
                "assistant_memory_count": profile.memory_count,
            }
        )
    except DatabaseError:
        pass
    return context
