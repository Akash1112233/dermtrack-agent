import hashlib
from typing import Any

from database.schemas import KnowledgeDocument


class KnowledgeIngestionService:
    """Chunk, embed, and persist RAG knowledge documents."""

    def __init__(self, chunker: Any, embedding_service: Any, repository: Any):
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.repository = repository

    def ingest(self, document: KnowledgeDocument, pages: list[Any] | None = None) -> int:
        """Ingest a document and return the number of saved chunks."""
        if pages is not None and hasattr(self.chunker, "split_pages"):
            page_chunks = self.chunker.split_pages(pages)
            chunks = [chunk.text for chunk in page_chunks]
            chunk_metadata = [
                {"page_number": str(chunk.page_number)} for chunk in page_chunks
            ]
        else:
            chunks = self.chunker.split(document.content)
            chunk_metadata = [{} for _ in chunks]

        if not chunks:
            raise ValueError("Knowledge document produced no chunks.")

        embeddings = self.embedding_service.embed_documents(chunks)
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts do not match.")

        content_hash = hashlib.sha256(document.content.encode("utf-8")).hexdigest()
        for index, (chunk, embedding, extra_metadata) in enumerate(
            zip(chunks, embeddings, chunk_metadata)
        ):
            chunk_document = KnowledgeDocument(
                source_id=f"{document.source_id}::chunk::{index}",
                title=f"{document.title} (chunk {index + 1})",
                content=chunk,
                source_type=document.source_type,
                url=document.url,
                tags=document.tags,
                metadata={
                    **document.metadata,
                    **extra_metadata,
                    "parent_source_id": document.source_id,
                    "chunk_index": str(index),
                    "content_hash": content_hash,
                },
                embedding=embedding,
            )
            self.repository.upsert(chunk_document)

        return len(chunks)
