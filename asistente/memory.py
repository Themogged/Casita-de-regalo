import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import AssistantConversation, AssistantMemory, AssistantMessage, AssistantProfile


EMBEDDING_DIMENSION = 96
MAX_RETRIEVAL_CANDIDATES = 200
SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:contrasena|contraseña|clave|cvv|cvc|codigo de seguridad)\b", re.I),
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
)
STOPWORDS = {
    "a", "al", "algo", "con", "de", "del", "el", "ella", "en", "es", "la", "las",
    "lo", "los", "me", "mi", "mis", "para", "por", "que", "se", "su", "sus", "un",
    "una", "y", "yo",
}


@dataclass(frozen=True)
class MemoryCandidate:
    category: str
    key: str
    content: str
    importance: int = 3
    is_sensitive: bool = False
    memory_type: str = AssistantMemory.MemoryType.OBSERVATION


def normalize_text(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9\s$.-]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _tokens(value):
    return [token for token in normalize_text(value).split() if len(token) > 1 and token not in STOPWORDS]


def build_embedding(value, dimension=EMBEDDING_DIMENSION):
    tokens = _tokens(value)
    features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
    vector = [0.0] * dimension
    for feature in features:
        digest = hashlib.sha256(feature.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return vector
    return [round(value / norm, 6) for value in vector]


def cosine_similarity(left, right):
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(float(a) * float(b) for a, b in zip(left, right))


def get_memory_profile(user):
    profile, created = AssistantProfile.objects.get_or_create(user=user)
    if created and not profile.allowed_categories:
        profile.allowed_categories = AssistantProfile.DEFAULT_CATEGORIES
        profile.save(update_fields=["allowed_categories", "updated_at"])
    return profile


def contains_sensitive_data(content):
    return any(pattern.search(str(content or "")) for pattern in SENSITIVE_PATTERNS)


def memory_is_safe(content):
    return not contains_sensitive_data(content)


def redact_sensitive_content(content):
    value = str(content or "")
    for pattern in SENSITIVE_PATTERNS:
        value = pattern.sub("[dato privado omitido]", value)
    return value


def extract_memory_candidate(message):
    normalized = normalize_text(message)
    person_match = re.search(
        r"(?:mi|para mi)\s+(pareja|espos[oa]|hij[oa]|mama|papa|amig[oa])\s+se llama\s+([a-z][a-z\s-]{1,45})",
        normalized,
        re.I,
    )
    if person_match:
        relationship = person_match.group(1).strip()
        name = person_match.group(2).strip(" .,-")
        return MemoryCandidate(
            AssistantMemory.Category.PEOPLE,
            f"important_person_{relationship}",
            f"{relationship}: {name}",
            4,
        )

    date_match = re.search(
        r"(nuestro aniversario|el cumpleanos de mi (?:pareja|espos[oa]|hij[oa]|mama|papa|amig[oa]))\s+(?:es|cae el)\s+([a-z0-9\s/-]{3,45})",
        normalized,
        re.I,
    )
    if date_match:
        subject = date_match.group(1).strip()
        value = date_match.group(2).strip(" .,-")
        key_suffix = re.sub(r"[^a-z0-9]+", "_", subject).strip("_")
        return MemoryCandidate(
            AssistantMemory.Category.DATES,
            f"special_date_{key_suffix}"[:90],
            f"{subject}: {value}",
            4,
            True,
        )

    patterns = (
        (r"(?:me llamo|mi nombre es)\s+([a-z][a-z\s-]{1,45})", "identity", "preferred_name", 4, False),
        (r"(?:mi color favorito es|prefiero (?:el )?color|me gusta (?:el )?color)\s+([a-z\s-]{3,40})", "preferences", "favorite_color", 3, False),
        (r"(?:mi estilo favorito es|prefiero (?:un )?estilo)\s+([a-z\s-]{3,60})", "preferences", "favorite_style", 3, False),
        (r"(?:mi presupuesto habitual es|suelo gastar)\s+([$0-9.\s-]{3,40})", "budget", "usual_budget", 4, False),
        (r"(?:prefiero pagar (?:con|por)|mi forma de pago preferida es)\s+([a-z\s-]{3,45})", "payment", "preferred_payment", 3, False),
        (r"(?:prefiero (?:la )?entrega|mi entrega preferida es)\s+([a-z\s-]{3,80})", "delivery", "preferred_delivery", 3, False),
        (r"(?:mi talla es|uso talla)\s+([a-z0-9\s-]{1,30})", "sizes", "usual_size", 4, True),
        (r"(?:mi direccion es|entregar en)\s+(.{8,120})", "delivery", "frequent_address", 5, True),
        (r"(?:mi regalo favorito es|me gusta regalar)\s+(.{3,100})", "products", "favorite_product", 3, False),
        (r"(?:prefiero personalizar con|mi personalizacion favorita es)\s+(.{3,100})", "personalization", "preferred_personalization", 3, False),
    )
    for pattern, category, key, importance, sensitive in patterns:
        match = re.search(pattern, normalized, re.I)
        if not match:
            continue
        value = match.group(1).strip(" .,-")
        if not value or len(value) > 140 or not memory_is_safe(value):
            return None
        memory_type = (
            AssistantMemory.MemoryType.PREFERENCE
            if category in {"preferences", "budget", "payment", "delivery", "sizes"}
            else AssistantMemory.MemoryType.OBSERVATION
        )
        return MemoryCandidate(category, key, value, importance, sensitive, memory_type)
    return None


def retrieve_relevant_memories(user, query, limit=6):
    profile = get_memory_profile(user)
    if not profile.is_memory_active:
        return []
    query_vector = build_embedding(query)
    now = timezone.now()
    AssistantMemory.objects.filter(user=user, expires_at__lte=now).delete()
    memories = list(
        AssistantMemory.objects.filter(
            user=user,
            consent_status=AssistantMemory.Consent.GRANTED,
            is_confirmed=True,
        ).exclude(expires_at__lte=now)[:MAX_RETRIEVAL_CANDIDATES]
    )
    allowed = set(profile.allowed_categories)
    scored = []
    for memory in memories:
        if memory.category not in allowed:
            continue
        score = cosine_similarity(query_vector, memory.embedding or [])
        score += memory.importance * 0.035
        if memory.key in {"preferred_name", "favorite_color", "favorite_style", "usual_budget"}:
            score += 0.08
        scored.append((score, memory))
    scored.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
    return [memory for score, memory in scored[:limit] if score >= 0.08]


@transaction.atomic
def save_memory_candidate(user, candidate, *, force=False, consent_granted=True):
    profile = get_memory_profile(user)
    if not profile.is_memory_active or not profile.category_is_allowed(candidate.category):
        return {"status": "disabled", "memory": None}
    if not memory_is_safe(candidate.content):
        return {"status": "rejected", "memory": None}

    existing = AssistantMemory.objects.select_for_update().filter(user=user, key=candidate.key).first()
    if existing and normalize_text(existing.content) != normalize_text(candidate.content) and not force:
        return {"status": "conflict", "memory": existing}

    if existing and normalize_text(existing.content) == normalize_text(candidate.content):
        existing.mention_count = min(existing.mention_count + 1, 999)
        if existing.mention_count >= 2 and existing.memory_type == AssistantMemory.MemoryType.OBSERVATION:
            existing.memory_type = AssistantMemory.MemoryType.PREFERENCE
        existing.save(update_fields=["mention_count", "memory_type", "updated_at"])
        return {"status": "reinforced", "memory": existing}

    consent_status = (
        AssistantMemory.Consent.GRANTED if consent_granted else AssistantMemory.Consent.PENDING
    )
    memory, _ = AssistantMemory.objects.update_or_create(
        user=user,
        key=candidate.key,
        defaults={
            "category": candidate.category,
            "content": candidate.content,
            "search_text": normalize_text(candidate.content),
            "embedding": build_embedding(candidate.content),
            "importance": candidate.importance,
            "memory_type": candidate.memory_type,
            "mention_count": 1,
            "source": AssistantMemory.Source.CHAT,
            "consent_status": consent_status,
            "is_sensitive": candidate.is_sensitive,
            "is_confirmed": consent_granted,
        },
    )
    return {"status": "saved" if consent_granted else "pending", "memory": memory}


def serialize_memory(memory):
    return {
        "id": memory.pk,
        "category": memory.category,
        "category_label": memory.get_category_display(),
        "key": memory.key,
        "content": memory.content,
        "importance": memory.importance,
        "memory_type": memory.memory_type,
        "memory_type_label": memory.get_memory_type_display(),
        "mention_count": memory.mention_count,
        "source": memory.get_source_display(),
        "sensitive": memory.is_sensitive,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
        "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
    }


def build_memory_context(memories):
    if not memories:
        return ""
    facts = "; ".join(f"{memory.get_category_display()}: {memory.content}" for memory in memories)
    return (
        "Datos confirmados y autorizados por el usuario, útiles solo si aplican a esta pregunta: "
        f"{facts}. No inventes datos ni menciones que provienen de una memoria."
    )


def record_conversation_turn(user, user_message, assistant_message):
    profile = get_memory_profile(user)
    if not profile.is_memory_active:
        return None
    safe_user_message = redact_sensitive_content(user_message)
    safe_assistant_message = redact_sensitive_content(assistant_message)
    conversation = (
        AssistantConversation.objects.filter(user=user, is_active=True).order_by("-updated_at").first()
    )
    if not conversation:
        conversation = AssistantConversation.objects.create(
            user=user,
            title=safe_user_message[:120],
        )
    AssistantMessage.objects.bulk_create(
        [
            AssistantMessage(conversation=conversation, role=AssistantMessage.Role.USER, content=safe_user_message),
            AssistantMessage(
                conversation=conversation,
                role=AssistantMessage.Role.ASSISTANT,
                content=safe_assistant_message,
            ),
        ]
    )
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])
    _compact_conversation(conversation, profile)
    return conversation


def _compact_conversation(conversation, profile):
    messages = list(conversation.messages.order_by("-created_at")[:80])
    if len(messages) < 60:
        return
    ordered = list(reversed(messages))
    summary_lines = [f"{message.role}: {message.content[:180]}" for message in ordered[:40]]
    summary = " | ".join(summary_lines)[-5000:]
    conversation.summary = summary
    conversation.save(update_fields=["summary", "updated_at"])
    profile.conversation_summary = summary
    profile.save(update_fields=["conversation_summary", "updated_at"])


def pause_memory(profile, days=1):
    profile.memory_paused_until = timezone.now() + timedelta(days=days)
    profile.save(update_fields=["memory_paused_until", "updated_at"])
