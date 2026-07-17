import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MemoryEditForm, MemorySettingsForm
from .memory import build_embedding, get_memory_profile, normalize_text, serialize_memory
from .models import AssistantMemory


@login_required
def memory_center(request):
    profile = get_memory_profile(request.user)
    memories = request.user.assistant_memories.all()
    return render(
        request,
        "asistente/memoria.html",
        {
            "memory_profile": profile,
            "memories": memories,
            "settings_form": MemorySettingsForm(instance=profile),
            "memory_categories": AssistantMemory.Category.choices,
        },
    )


@login_required
@require_POST
def update_memory_settings(request):
    profile = get_memory_profile(request.user)
    form = MemorySettingsForm(request.POST, instance=profile)
    if form.is_valid():
        updated = form.save(commit=False)
        updated.memory_paused_until = None
        updated.save()
        messages.success(request, "Preferencias de memoria actualizadas.")
    else:
        messages.error(request, "Revisa las opciones seleccionadas.")
    return redirect("assistant_memory")


@login_required
@require_POST
def pause_memory(request):
    profile = get_memory_profile(request.user)
    hours = request.POST.get("hours", "24")
    try:
        hours = max(1, min(int(hours), 24 * 30))
    except (TypeError, ValueError):
        hours = 24
    profile.memory_paused_until = timezone.now() + timedelta(hours=hours)
    profile.save(update_fields=["memory_paused_until", "updated_at"])
    messages.success(request, "La memoria quedó pausada temporalmente.")
    return redirect("assistant_memory")


@login_required
def edit_memory(request, memory_id):
    memory = get_object_or_404(AssistantMemory, pk=memory_id, user=request.user)
    if request.method == "POST":
        form = MemoryEditForm(request.POST, instance=memory)
        if form.is_valid():
            edited = form.save(commit=False)
            edited.search_text = normalize_text(edited.content)
            edited.embedding = build_embedding(edited.content)
            edited.source = AssistantMemory.Source.MANUAL
            edited.is_confirmed = True
            edited.consent_status = AssistantMemory.Consent.GRANTED
            edited.save()
            messages.success(request, "Recuerdo actualizado.")
            return redirect("assistant_memory")
    else:
        form = MemoryEditForm(instance=memory)
    return render(request, "asistente/memoria_editar.html", {"memory": memory, "form": form})


@login_required
@require_POST
def delete_memory(request, memory_id):
    memory = get_object_or_404(AssistantMemory, pk=memory_id, user=request.user)
    memory.delete()
    messages.success(request, "Recuerdo eliminado.")
    return redirect("assistant_memory")


@login_required
@require_POST
def clear_memory(request):
    request.user.assistant_memories.all().delete()
    profile = get_memory_profile(request.user)
    profile.conversation_summary = ""
    profile.save(update_fields=["conversation_summary", "updated_at"])
    request.user.assistant_conversations.all().delete()
    messages.success(request, "La memoria del asistente fue eliminada por completo.")
    return redirect("assistant_memory")


@login_required
def export_memory(request):
    profile = get_memory_profile(request.user)
    payload = {
        "exported_at": timezone.now().isoformat(),
        "user": request.user.get_username(),
        "memory_enabled": profile.memory_enabled,
        "allowed_categories": profile.allowed_categories,
        "memories": [serialize_memory(memory) for memory in request.user.assistant_memories.all()],
    }
    response = HttpResponse(
        json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = 'attachment; filename="memoria-cora.json"'
    return response


@login_required
def memory_status(request):
    profile = get_memory_profile(request.user)
    return JsonResponse(
        {
            "ok": True,
            "enabled": profile.memory_enabled,
            "active": profile.is_memory_active,
            "count": request.user.assistant_memories.count(),
            "settings_url": reverse("assistant_memory"),
        }
    )
