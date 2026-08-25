from database.schemas import KnowledgeDocument
from rag.chroma_store import ChromaVectorStore


class FakeCollection:
    def __init__(self):
        self.upsert_calls = []
        self.deleted = []

    def upsert(self, **kwargs):
        self.upsert_calls.append(kwargs)

    def query(self, **kwargs):
        return {
            "ids": [["source::chunk::0"]],
            "documents": [["trusted guidance"]],
            "metadatas": [[
                {
                    "title": "Trusted guidance (chunk 1)",
                    "source_type": "clinical_reference",
                    "url": "https://example.org/guidance",
                    "tags": '["skin"]',
                    "parent_source_id": "source",
                    "chunk_index": "0",
                }
            ]],
            "distances": [[0.25]],
        }

    def get(self, **kwargs):
        return {"ids": ["source::chunk::0"]}

    def delete(self, **kwargs):
        self.deleted.extend(kwargs["ids"])


class FakeClient:
    def __init__(self, collection):
        self.collection = collection

    def get_or_create_collection(self, name):
        assert name == "dermtrack_knowledge"
        return self.collection


def make_document():
    return KnowledgeDocument(
        source_id="source::chunk::0",
        title="Trusted guidance (chunk 1)",
        content="trusted guidance",
        source_type="clinical_reference",
        url="https://example.org/guidance",
        tags=["skin"],
        metadata={"parent_source_id": "source", "chunk_index": "0"},
        embedding=[0.1, 0.2],
    )


def test_chroma_store_upserts_embedding_and_metadata():
    collection = FakeCollection()
    store = ChromaVectorStore(client=FakeClient(collection))

    document = store.upsert(make_document())

    assert document.source_id == "source::chunk::0"
    call = collection.upsert_calls[0]
    assert call["ids"] == ["source::chunk::0"]
    assert call["embeddings"] == [[0.1, 0.2]]
    assert call["metadatas"][0]["parent_source_id"] == "source"


def test_chroma_store_returns_normalized_similarity_results():
    store = ChromaVectorStore(client=FakeClient(FakeCollection()))

    results = store.similarity_search([0.1, 0.2], limit=2)

    assert results[0]["document"].source_id == "source::chunk::0"
    assert results[0]["document"].tags == ["skin"]
    assert results[0]["score"] == 0.8


def test_chroma_store_deletes_chunks_by_parent_source():
    collection = FakeCollection()
    store = ChromaVectorStore(client=FakeClient(collection))

    deleted = store.delete_by_source("source")

    assert deleted == 1
    assert collection.deleted == ["source::chunk::0"]
