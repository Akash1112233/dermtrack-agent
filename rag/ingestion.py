from typing import Any

from database.schemas import KnowledgeDocument

class KnowledgeIngestionService:
    """Chunk, embed, and persist RAG knowledge documents."""

    def __init__(
        self,
        chunker: Any,
        embedding_service: Any,
        repository: Any,
    ):
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.repository = repository

    def ingest(self, document: KnowledgeDocument) -> int:
        """Ingest a document and return the number of saved chunks."""
        chunks = self.chunker.split(document.content)

        if not chunks:
            raise ValueError(
                "Knowledge document produced no chunks."
            )

        embeddings = self.embedding_service.embed_documents(
            chunks
        )

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Chunk and embedding counts do not match."
            )

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            chunk_document = KnowledgeDocument(
                source_id=(
                    f"{document.source_id}::chunk::{index}"
                ),
                title=(
                    f"{document.title} "
                    f"(chunk {index + 1})"
                ),
                content=chunk,
                source_type=document.source_type,
                url=document.url,
                tags=document.tags,
                metadata={
                    **document.metadata,
                    "parent_source_id": document.source_id,
                    "chunk_index": str(index),
                },
                embedding=embedding,
            )

            self.repository.upsert(chunk_document)

        return len(chunks)