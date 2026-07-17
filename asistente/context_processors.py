def assistant_account_context(request):
    context = {
        "assistant_memory_enabled": False,
        "assistant_memory_active": False,
        "assistant_memory_count": 0,
    }
    if not request.user.is_authenticated:
        return context
    try:
        profile = request.user.assistant_profile
        context.update(
            {
                "assistant_memory_enabled": profile.memory_enabled,
                "assistant_memory_active": profile.is_memory_active,
                "assistant_memory_count": request.user.assistant_memories.count(),
            }
        )
    except Exception:
        pass
    return context
