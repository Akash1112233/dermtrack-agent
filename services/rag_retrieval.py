from typing import Any

from database.schemas import RetrievedSource

class RAGRetrievalService:
    """Retrieve relevant knowledge sources for a consultation."""

    def __init__(
        self,
        embedding_service: Any,
        repository: Any,
    ):
        self.embedding_service = embedding_service
        self.repository = repository

    def retrieve(
        self,
        query: str,
        limit: int = 4,
    ) -> list[RetrievedSource]:
        """Return the most relevant knowledge sources."""
        if not query.strip():
            raise ValueError("query cannot be empty.")

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        query_embedding = self.embedding_service.embed_text(
            query
        )

        search_results = self.repository.similarity_search(
            query_embedding,
            limit,
        )

        sources = []

        for result in search_results:
            document = result["document"]
            score = float(result["score"])

            sources.append(
                RetrievedSource(
                    source_id=document.source_id,
                    title=document.title,
                    url=document.url,
                    similarity_score=score,
                )
            )

        return sources