from django import forms

from .models import AssistantMemory, AssistantProfile


class MemorySettingsForm(forms.ModelForm):
    allowed_categories = forms.MultipleChoiceField(
        choices=AssistantMemory.Category.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = AssistantProfile
        fields = ("memory_enabled", "allowed_categories")


class MemoryEditForm(forms.ModelForm):
    class Meta:
        model = AssistantMemory
        fields = ("category", "memory_type", "content", "importance", "expires_at")
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "content": forms.Textarea(attrs={"rows": 3, "maxlength": 600}),
        }
