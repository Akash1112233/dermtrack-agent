from typing import Any

from agents.workflow import build_consultation_graph
from app.config import Settings, get_settings
from database.container import Repositories, build_repositories
from services.gemini_embeddings import GeminiEmbeddingService
from services.gemini_response import GeminiResponseService
from services.gemini_vision import GeminiVisionService
from services.groq_service import GroqTranscriptionService
from services.rag_retrieval import RAGRetrievalService
from services.triage_service import SafetyTriageService

class ConsultationApplication:
    """Production application service for consultations."""

    def __init__(
        self,
        settings: Settings | None = None,
        repositories: Repositories | Any | None = None,
        transcription_service: Any | None = None,
        vision_service: Any | None = None,
        retrieval_service: Any | None = None,
        response_service: Any | None = None,
    ):
        needs_configuration = (
            settings is None
            and (
                repositories is None
                or transcription_service is None
                or vision_service is None
                or retrieval_service is None
                or response_service is None
            )
        )

        configured_settings = (
            settings
            or (get_settings() if needs_configuration else None)
        )

        if repositories is None:
            repositories = build_repositories(
                settings=configured_settings
            )

        self.repositories = repositories
        self.consultation_repository = (
            repositories.consultations
        )

        if transcription_service is None:
            transcription_service = (
                GroqTranscriptionService(
                    api_key=configured_settings.groq_api_key,
                    model=(
                        configured_settings
                        .groq_transcription_model
                    ),
                )
            )

        if vision_service is None:
            vision_service = GeminiVisionService(
                api_key=configured_settings.google_api_key,
                model_name=configured_settings.gemini_model,
            )

        if retrieval_service is None:
            embedding_service = GeminiEmbeddingService(
                api_key=configured_settings.google_api_key,
                model_name=(
                    configured_settings
                    .gemini_embedding_model
                ),
            )

            retrieval_service = RAGRetrievalService(
                embedding_service=embedding_service,
                repository=repositories.knowledge_documents,
            )

        if response_service is None:
            response_service = GeminiResponseService(
                api_key=configured_settings.google_api_key,
                model_name=configured_settings.gemini_model,
            )

        self.graph = build_consultation_graph(
            transcription_service=transcription_service,
            vision_service=vision_service,
            triage_service=SafetyTriageService(),
            retrieval_service=retrieval_service,
            response_service=response_service,
            consultation_repository=(
                repositories.consultations
            ),
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run a consultation through the workflow."""
        return self.graph.invoke(state)