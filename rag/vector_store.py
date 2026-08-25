from typing import Any, Protocol

from database.schemas import KnowledgeDocument


class VectorStore(Protocol):
    """Provider-neutral interface for semantic knowledge retrieval."""

    def upsert(self, document: KnowledgeDocument) -> KnowledgeDocument:
        """Insert or replace one embedded document chunk."""
        ...

    def similarity_search(
        self,
        query_embedding: list[float],
        limit: int = 4,
    ) -> list[dict[str, Any]]:
        """Return documents ordered by descending similarity."""
        ...

    def delete_by_source(self, source_id: str) -> int:
        """Delete chunks belonging to a parent source and return count."""
        ...
