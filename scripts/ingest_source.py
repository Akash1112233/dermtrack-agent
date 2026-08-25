"""Ingest a local text, Markdown, or PDF source into the DermTrack RAG index."""

import argparse
from pathlib import Path

from app.config import get_settings
from database.container import build_repositories
from database.schemas import KnowledgeDocument
from rag.chroma_store import ChromaVectorStore
from rag.chunking import DocumentChunker
from rag.document_loader import load_document
from rag.ingestion import KnowledgeIngestionService
from services.gemini_embeddings import GeminiEmbeddingService


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--source-type", default="clinical_reference")
    parser.add_argument("--trust-tier", default="authoritative")
    parser.add_argument("--tag", action="append", default=[])
    args = parser.parse_args()

    pages = load_document(args.file)
    content = "\n\n".join(page.text for page in pages).strip()
    if not content:
        raise ValueError("The source file contains no extractable text.")

    settings = get_settings()
    repositories = build_repositories(settings=settings)
    repository = repositories.knowledge_documents
    if settings.vector_store_backend.lower() == "chroma":
        repository = ChromaVectorStore(
            persist_directory=settings.chroma_persist_directory,
            collection_name=settings.chroma_collection_name,
        )
    document = KnowledgeDocument(
        source_id=args.source_id,
        title=args.title,
        content=content,
        source_type=args.source_type,
        url=args.url,
        tags=args.tag,
        metadata={
            "filename": args.file.name,
            "language": "en",
            "trust_tier": args.trust_tier,
            "page_count": str(len(pages)),
        },
    )
    service = KnowledgeIngestionService(
        chunker=DocumentChunker(chunk_size=700, chunk_overlap=100),
        embedding_service=GeminiEmbeddingService(
            api_key=settings.google_api_key,
            model_name=settings.gemini_embedding_model,
        ),
        repository=repository,
    )
    saved_chunks = service.ingest(document, pages=pages)
    print(f"Ingested source: {args.source_id}")
    print(f"Pages with text: {len(pages)}")
    print(f"Saved chunks: {saved_chunks}")


if __name__ == "__main__":
    main()
