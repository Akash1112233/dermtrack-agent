import pytest

from services.gemini_embeddings import GeminiEmbeddingService

class FakeEmbeddings:
    def embed_query(self, text):
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts):
        return [
            [0.1, 0.2, 0.3]
            for _ in texts
        ]

def test_embedding_service_embeds_single_text():
    service = GeminiEmbeddingService(
        api_key="test-key",
        model_name="gemini-embedding-001",
        embeddings=FakeEmbeddings(),
    )

    embedding = service.embed_text("General skin-care guidance.")

    assert embedding == [0.1, 0.2, 0.3]

def test_embedding_service_embeds_multiple_documents():
    service = GeminiEmbeddingService(
        api_key="test-key",
        model_name="gemini-embedding-001",
        embeddings=FakeEmbeddings(),
    )

    embeddings = service.embed_documents(
        [
            "First knowledge chunk.",
            "Second knowledge chunk.",
        ]
    )

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert embeddings[1] == [0.1, 0.2, 0.3]

def test_embedding_service_rejects_empty_text():
    service = GeminiEmbeddingService(
        api_key="test-key",
        model_name="gemini-embedding-001",
        embeddings=FakeEmbeddings(),
    )

    with pytest.raises(ValueError, match="text cannot be empty"):
        service.embed_text("   ")

def test_embedding_service_rejects_empty_document_list():
    service = GeminiEmbeddingService(
        api_key="test-key",
        model_name="gemini-embedding-001",
        embeddings=FakeEmbeddings(),
    )

    with pytest.raises(ValueError, match="documents cannot be empty"):
        service.embed_documents([])