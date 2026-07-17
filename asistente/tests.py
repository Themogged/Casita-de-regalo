import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .memory import (
    MemoryCandidate,
    build_embedding,
    extract_memory_candidate,
    get_memory_profile,
    retrieve_relevant_memories,
    save_memory_candidate,
)
from .models import AssistantConversation, AssistantMemory
from pedidos.models import Pedido


class AssistantMemoryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="cliente-cora",
            email="cliente@example.com",
            password="ClaveSegura123!",
        )
        self.client.force_login(self.user)
        self.profile = get_memory_profile(self.user)
        self.profile.memory_enabled = True
        self.profile.allowed_categories = self.profile.DEFAULT_CATEGORIES
        self.profile.save(update_fields=["memory_enabled", "allowed_categories", "updated_at"])

    def post_chat(self, message, **extra):
        payload = {"message": message, "history": [], **extra}
        return self.client.post(
            reverse("assistant_chat"),
            data=json.dumps(payload),
            content_type="application/json",
            secure=True,
        )

    def test_embedding_local_es_determinista_y_recupera_contexto_relevante(self):
        first = build_embedding("Prefiero regalos rosados")
        second = build_embedding("Prefiero regalos rosados")
        self.assertEqual(first, second)
        save_memory_candidate(
            self.user,
            MemoryCandidate("preferences", "favorite_color", "rosa suave", 4),
        )

        memories = retrieve_relevant_memories(self.user, "Recomiendame algo de color rosa")

        self.assertEqual(memories[0].key, "favorite_color")

    def test_chat_guarda_preferencia_confirmada_y_refuerza_repeticiones(self):
        first = self.post_chat("Mi color favorito es rosa suave")
        second = self.post_chat("Mi color favorito es rosa suave")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        memory = AssistantMemory.objects.get(user=self.user, key="favorite_color")
        self.assertEqual(memory.content, "rosa suave")
        self.assertEqual(memory.mention_count, 2)
        self.assertTrue(AssistantConversation.objects.filter(user=self.user).exists())

    def test_extrae_persona_importante_y_fecha_sin_convertirlas_en_supuestos(self):
        person = extract_memory_candidate("Mi pareja se llama Laura")
        special_date = extract_memory_candidate("Nuestro aniversario es 15 de mayo")

        self.assertEqual(person.category, AssistantMemory.Category.PEOPLE)
        self.assertEqual(person.content, "pareja: laura")
        self.assertEqual(special_date.category, AssistantMemory.Category.DATES)
        self.assertTrue(special_date.is_sensitive)

    def test_asistente_informa_estado_real_del_ultimo_pedido(self):
        order = Pedido.objects.create(
            usuario=self.user,
            total="94000.00",
            estado="confirmado",
        )

        response = self.post_chat("Cual es el estado de mi pedido?")

        self.assertEqual(response.status_code, 200)
        self.assertIn(f"#{order.pk}", response.json()["reply"])
        self.assertIn("confirmado", response.json()["reply"].lower())

    def test_chat_pide_confirmacion_antes_de_actualizar_un_dato_contradictorio(self):
        self.post_chat("Mi color favorito es rosa")

        conflict = self.post_chat("Mi color favorito es azul")
        confirmed = self.post_chat("Si, actualizar")

        self.assertEqual(conflict.json()["memory_event"], "conflict")
        self.assertEqual(confirmed.json()["memory_event"], "saved")
        self.assertEqual(
            AssistantMemory.objects.get(user=self.user, key="favorite_color").content,
            "azul",
        )

    def test_dato_privado_requiere_consentimiento_explicito(self):
        response = self.post_chat("Mi direccion es Calle 10 numero 20-30")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["memory_event"], "consent_required")
        self.assertFalse(AssistantMemory.objects.filter(user=self.user, key="frequent_address").exists())

        confirmed = self.post_chat("Si, guardar")

        self.assertEqual(confirmed.json()["memory_event"], "saved")
        memory = AssistantMemory.objects.get(user=self.user, key="frequent_address")
        self.assertTrue(memory.is_sensitive)
        self.assertEqual(memory.consent_status, AssistantMemory.Consent.GRANTED)

    def test_chat_rechaza_contrasenas_y_datos_de_tarjeta(self):
        response = self.post_chat("Mi contrasena es NoLaGuardes123")

        self.assertEqual(response.status_code, 400)
        self.assertIn("no envies", response.json()["message"].lower().replace("í", "i"))
        self.assertFalse(AssistantMemory.objects.filter(user=self.user).exists())
        self.assertFalse(AssistantConversation.objects.filter(user=self.user).exists())

    def test_conversacion_privada_no_guarda_historial_ni_preferencia(self):
        session = self.client.session
        session["assistant_history"] = [
            {"role": "user", "text": "Mi color favorito es azul"},
        ]
        session.save()

        response = self.post_chat("Mi color favorito es lavanda", private_session=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(AssistantMemory.objects.filter(user=self.user).exists())
        self.assertFalse(AssistantConversation.objects.filter(user=self.user).exists())
        self.assertEqual(
            self.client.session["assistant_history"][0]["text"],
            "Mi color favorito es azul",
        )

    def test_usuario_controla_categorias_y_puede_exportar_y_borrar(self):
        save_memory_candidate(
            self.user,
            MemoryCandidate("preferences", "favorite_style", "minimalista", 3),
        )
        export = self.client.get(reverse("assistant_memory_export"), secure=True)

        self.assertEqual(export.status_code, 200)
        payload = json.loads(export.content)
        self.assertEqual(payload["user"], self.user.username)
        self.assertEqual(payload["memories"][0]["key"], "favorite_style")

        clear = self.client.post(reverse("assistant_memory_clear"), secure=True)

        self.assertRedirects(clear, reverse("assistant_memory"))
        self.assertFalse(AssistantMemory.objects.filter(user=self.user).exists())

    def test_memoria_inicia_desactivada_para_usuario_nuevo(self):
        other = get_user_model().objects.create_user("sin-memoria")
        profile = get_memory_profile(other)

        self.assertFalse(profile.memory_enabled)
        self.assertFalse(profile.is_memory_active)
