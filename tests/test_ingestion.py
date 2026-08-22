from database.schemas import KnowledgeDocument
from rag.ingestion import KnowledgeIngestionService

class FakeChunker:
    def split(self, text):
        return [
            "First knowledge chunk.",
            "Second knowledge chunk.",
        ]

class FakeEmbeddingService:
    def embed_documents(self, documents):
        return [
            [0.1, 0.2, 0.3]
            for _ in documents
        ]

class FakeKnowledgeRepository:
    def __init__(self):
        self.saved_documents = []

    def upsert(self, document):
        self.saved_documents.append(document)
        return document

def make_document():
    return KnowledgeDocument(
        source_id="source_001",
        title="Skin irritation guidance",
        content="Long skin-care guidance content.",
        source_type="clinical_guideline",
        url="https://example.com/skin-guidance",
        tags=["irritation"],
    )

def test_ingestion_chunks_embeds_and_saves_document():
    repository = FakeKnowledgeRepository()

    service = KnowledgeIngestionService(
        chunker=FakeChunker(),
        embedding_service=FakeEmbeddingService(),
        repository=repository,
    )

    result = service.ingest(make_document())

    assert result == 2
    assert len(repository.saved_documents) == 2

    first_chunk = repository.saved_documents[0]

    assert first_chunk.source_id == "source_001::chunk::0"
    assert first_chunk.content == "First knowledge chunk."
    assert first_chunk.embedding == [0.1, 0.2, 0.3]
    assert first_chunk.metadata["parent_source_id"] == "source_001"

def test_ingestion_rejects_documents_without_chunks():
    class EmptyChunker:
        def split(self, text):
            return []

    service = KnowledgeIngestionService(
        chunker=EmptyChunker(),
        embedding_service=FakeEmbeddingService(),
        repository=FakeKnowledgeRepository(),
    )

    try:
        service.ingest(make_document())
    except ValueError as error:
        assert "no chunks" in str(error).lower()
    else:
        raise AssertionError(
            "Ingestion should reject documents without chunks."
        )