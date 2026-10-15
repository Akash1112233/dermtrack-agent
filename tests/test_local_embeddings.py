import pytest

from services.local_embeddings import LocalEmbeddingService


class FakeSentenceTransformer:
    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True):
        if isinstance(texts, str):
            return [0.1, 0.2, 0.3]
        return [[0.1, 0.2, 0.3] for _ in texts]


def test_local_embedding_service_embeds_single_text():
    service = LocalEmbeddingService(
        model_name="test-model",
        model=FakeSentenceTransformer(),
    )

    assert service.embed_text("skin symptoms") == [0.1, 0.2, 0.3]


def test_local_embedding_service_embeds_documents():
    service = LocalEmbeddingService(
        model_name="test-model",
        model=FakeSentenceTransformer(),
    )

    result = service.embed_documents(["first chunk", "second chunk"])

    assert result == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]


def test_local_embedding_service_rejects_empty_input():
    service = LocalEmbeddingService(
        model_name="test-model",
        model=FakeSentenceTransformer(),
    )

    with pytest.raises(ValueError, match="text cannot be empty"):
        service.embed_text("   ")

    with pytest.raises(ValueError, match="documents cannot be empty"):
        service.embed_documents([])
