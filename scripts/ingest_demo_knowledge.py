from app.config import get_settings
from database.container import build_repositories
from database.schemas import KnowledgeDocument
from rag.chunking import DocumentChunker
from rag.ingestion import KnowledgeIngestionService
from services.gemini_embeddings import GeminiEmbeddingService

def main() -> None:
    settings = get_settings()
    repositories = build_repositories(settings=settings)

    document = KnowledgeDocument(
        source_id="demo_skin_guidance_v1",
        title="General skin-care guidance",
        content=(
            "This is educational demo content for DermTrack Agent. "
            "General skin-care guidance should be based on trusted "
            "sources and individual circumstances. Patients should "
            "monitor changes over time and seek qualified medical "
            "evaluation for persistent, worsening, or concerning "
            "symptoms. This information is not a diagnosis and "
            "does not replace professional medical advice."
        ),
        source_type="educational_demo",
        url="https://www.aad.org/",
        tags=[
            "skin-care",
            "education",
            "demo",
        ],
        metadata={
            "language": "en",
            "version": "1",
        },
    )

    chunker = DocumentChunker(
        chunk_size=300,
        chunk_overlap=40,
    )

    embedding_service = GeminiEmbeddingService(
        api_key=settings.google_api_key,
        model_name=settings.gemini_embedding_model,
    )

    ingestion_service = KnowledgeIngestionService(
        chunker=chunker,
        embedding_service=embedding_service,
        repository=repositories.knowledge_documents,
    )

    saved_chunks = ingestion_service.ingest(document)

    print("RAG ingestion successful")
    print(f"Saved chunks: {saved_chunks}")

if __name__ == "__main__":
    main()