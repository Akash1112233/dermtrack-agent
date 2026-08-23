"""Ingest a local text or Markdown source into the DermTrack RAG index."""

import argparse
from pathlib import Path

from app.config import get_settings
from database.container import build_repositories
from database.schemas import KnowledgeDocument
from rag.chunking import DocumentChunker
from rag.ingestion import KnowledgeIngestionService
from services.gemini_embeddings import GeminiEmbeddingService


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--source-type", default="clinical_reference")
    parser.add_argument("--tag", action="append", default=[])
    args = parser.parse_args()

    content = args.file.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError("The source file is empty.")

    settings = get_settings()
    repositories = build_repositories(settings=settings)
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
        },
    )
    service = KnowledgeIngestionService(
        chunker=DocumentChunker(chunk_size=700, chunk_overlap=100),
        embedding_service=GeminiEmbeddingService(
            api_key=settings.google_api_key,
            model_name=settings.gemini_embedding_model,
        ),
        repository=repositories.knowledge_documents,
    )
    saved_chunks = service.ingest(document)
    print(f"Ingested source: {args.source_id}")
    print(f"Saved chunks: {saved_chunks}")


if __name__ == "__main__":
    main()
