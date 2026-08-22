import pytest

from database.schemas import KnowledgeDocument
from services.rag_retrieval import RAGRetrievalService

class FakeEmbeddingService:
    def embed_text(self, text):
        return [0.1, 0.2, 0.3]

class FakeKnowledgeRepository:
    def similarity_search(self, embedding, limit):
        assert embedding == [0.1, 0.2, 0.3]
        assert limit == 2

        return [
            {
                "document": KnowledgeDocument(
                    source_id="source_001::chunk::0",
                    title="Skin irritation guidance",
                    content="General skin irritation information.",
                    source_type="clinical_guideline",
                    url="https://example.com/skin-guidance",
                    tags=["irritation"],
                    embedding=[0.1, 0.2, 0.3],
                ),
                "score": 0.92,
            }
        ]

def test_retrieval_returns_relevant_sources():
    service = RAGRetrievalService(
        embedding_service=FakeEmbeddingService(),
        repository=FakeKnowledgeRepository(),
    )

    sources = service.retrieve(
        query="What should I know about skin irritation?",
        limit=2,
    )

    assert len(sources) == 1
    assert sources[0].source_id == "source_001::chunk::0"
    assert sources[0].title == "Skin irritation guidance"
    assert sources[0].similarity_score == 0.92

def test_retrieval_rejects_empty_query():
    service = RAGRetrievalService(
        embedding_service=FakeEmbeddingService(),
        repository=FakeKnowledgeRepository(),
    )

    with pytest.raises(ValueError, match="query cannot be empty"):
        service.retrieve(query="   ")

def test_retrieval_rejects_invalid_limit():
    service = RAGRetrievalService(
        embedding_service=FakeEmbeddingService(),
        repository=FakeKnowledgeRepository(),
    )

    with pytest.raises(ValueError, match="limit"):
        service.retrieve(
            query="skin irritation",
            limit=0,
        )