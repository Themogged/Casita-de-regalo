from django.contrib import admin

from .models import AssistantConversation, AssistantMemory, AssistantMessage, AssistantProfile


@admin.register(AssistantProfile)
class AssistantProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "memory_enabled", "memory_paused_until", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AssistantMemory)
class AssistantMemoryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "category",
        "key",
        "memory_type",
        "mention_count",
        "importance",
        "consent_status",
        "updated_at",
    )
    list_filter = ("category", "memory_type", "consent_status", "is_sensitive", "is_confirmed")
    search_fields = ("user__username", "content", "key")
    readonly_fields = ("embedding", "search_text", "created_at", "updated_at")


class AssistantMessageInline(admin.TabularInline):
    model = AssistantMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False


@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("user__username", "title", "summary")
    readonly_fields = ("created_at", "updated_at")
    inlines = (AssistantMessageInline,)
