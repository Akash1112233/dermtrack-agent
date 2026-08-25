import json
from pathlib import Path
from typing import Any

from database.schemas import KnowledgeDocument


class ChromaVectorStore:
    """ChromaDB adapter implementing the provider-neutral vector-store API."""

    def __init__(
        self,
        persist_directory: str | Path = "data/chroma",
        collection_name: str = "dermtrack_knowledge",
        client: Any | None = None,
    ):
        if client is None:
            try:
                import chromadb
            except ImportError as error:
                raise RuntimeError(
                    "ChromaDB is not installed. Add the chromadb dependency "
                    "before creating ChromaVectorStore."
                ) from error
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(persist_directory))

        self.collection = client.get_or_create_collection(name=collection_name)

    def upsert(self, document: KnowledgeDocument) -> KnowledgeDocument:
        if not document.embedding:
            raise ValueError("document.embedding cannot be empty.")

        metadata = {
            "title": document.title,
            "source_type": document.source_type,
            "url": str(document.url),
            "tags": json.dumps(document.tags),
            **document.metadata,
        }
        self.collection.upsert(
            ids=[document.source_id],
            documents=[document.content],
            embeddings=[document.embedding],
            metadatas=[metadata],
        )
        return document

    def similarity_search(
        self,
        query_embedding: list[float],
        limit: int = 4,
    ) -> list[dict[str, Any]]:
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        matches: list[dict[str, Any]] = []
        for source_id, content, metadata, distance in zip(
            ids, documents, metadatas, distances
        ):
            metadata = metadata or {}
            tags = metadata.pop("tags", "[]")
            try:
                parsed_tags = json.loads(tags)
            except (TypeError, json.JSONDecodeError):
                parsed_tags = []
            document = KnowledgeDocument(
                source_id=source_id,
                title=metadata.pop("title", source_id),
                content=content,
                source_type=metadata.pop("source_type", "unknown"),
                url=metadata.pop("url"),
                tags=parsed_tags,
                metadata={str(key): str(value) for key, value in metadata.items()},
            )
            similarity = 1.0 / (1.0 + max(float(distance), 0.0))
            matches.append({"document": document, "score": similarity})
        return matches

    def delete_by_source(self, source_id: str) -> int:
        result = self.collection.get(where={"parent_source_id": source_id})
        ids = result.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)
