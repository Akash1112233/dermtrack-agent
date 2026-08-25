from typing import Any

from agents.workflow import build_consultation_graph
from app.config import Settings, get_settings
from database.container import Repositories, build_repositories
from rag.chroma_store import ChromaVectorStore
from services.deepgram_service import DeepgramService
from services.gemini_embeddings import GeminiEmbeddingService
from services.gemini_response import GeminiResponseService
from services.gemini_vision import GeminiVisionService
from services.rag_retrieval import RAGRetrievalService
from services.tavily_service import TavilyService
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
        needs_configuration = settings is None and (
            repositories is None
            or transcription_service is None
            or vision_service is None
            or retrieval_service is None
            or response_service is None
        )
        configured_settings = settings or (get_settings() if needs_configuration else None)

        if repositories is None:
            repositories = build_repositories(settings=configured_settings)

        self.repositories = repositories
        self.consultation_repository = repositories.consultations
        self.image_repository = getattr(repositories, "images", None)

        if transcription_service is None:
            transcription_service = DeepgramService(
                api_key=configured_settings.deepgram_api_key,
                stt_model=configured_settings.deepgram_stt_model,
                tts_model=configured_settings.deepgram_tts_model,
            )
        self.transcription_service = transcription_service
        self.deepgram_service = (
            transcription_service if hasattr(transcription_service, "synthesize") else None
        )

        if vision_service is None:
            vision_service = GeminiVisionService(
                api_key=configured_settings.google_api_key,
                model_name=configured_settings.gemini_model,
            )

        if retrieval_service is None:
            embedding_service = GeminiEmbeddingService(
                api_key=configured_settings.google_api_key,
                model_name=configured_settings.gemini_embedding_model,
            )
            vector_repository = repositories.knowledge_documents
            if configured_settings.vector_store_backend.lower() == "chroma":
                vector_repository = ChromaVectorStore(
                    persist_directory=configured_settings.chroma_persist_directory,
                    collection_name=configured_settings.chroma_collection_name,
                )
            retrieval_service = RAGRetrievalService(
                embedding_service=embedding_service,
                repository=vector_repository,
            )

        if response_service is None:
            response_service = GeminiResponseService(
                api_key=configured_settings.google_api_key,
                model_name=configured_settings.gemini_model,
            )

        tavily_service = None
        if configured_settings is not None and configured_settings.tavily_enabled:
            allowed_domains = [
                domain.strip()
                for domain in configured_settings.tavily_allowed_domains.split(",")
                if domain.strip()
            ]
            tavily_service = TavilyService(
                api_key=configured_settings.tavily_api_key,
                api_url=configured_settings.tavily_api_url,
                allowed_domains=allowed_domains,
                max_results=configured_settings.tavily_max_results,
                timeout_seconds=configured_settings.tavily_timeout_seconds,
            )

        self.graph = build_consultation_graph(
            transcription_service=transcription_service,
            vision_service=vision_service,
            triage_service=SafetyTriageService(),
            retrieval_service=retrieval_service,
            response_service=response_service,
            consultation_repository=repositories.consultations,
            tavily_service=tavily_service,
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run a consultation through the workflow."""
        return self.graph.invoke(state)
