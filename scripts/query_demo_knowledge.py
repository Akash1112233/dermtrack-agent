from app.config import get_settings
from database.container import build_repositories
from services.gemini_embeddings import GeminiEmbeddingService
from services.rag_retrieval import RAGRetrievalService

def main() -> None:
    settings = get_settings()
    repositories = build_repositories(settings=settings)

    embedding_service = GeminiEmbeddingService(
        api_key=settings.google_api_key,
        model_name=settings.gemini_embedding_model,
    )

    retrieval_service = RAGRetrievalService(
        embedding_service=embedding_service,
        repository=repositories.knowledge_documents,
    )

    sources = retrieval_service.retrieve(
        query=(
            "What should patients know about persistent "
            "or worsening skin symptoms?"
        ),
        limit=2,
    )

    if not sources:
        raise RuntimeError(
            "Vector retrieval returned no sources."
        )

    print("RAG vector retrieval successful")

    for source in sources:
        print(f"Source ID: {source.source_id}")
        print(f"Title: {source.title}")
        print(f"Similarity score: {source.similarity_score}")
        print(f"URL: {source.url}")
        print("---")

if __name__ == "__main__":
    main()