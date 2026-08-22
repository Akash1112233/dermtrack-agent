from database.repositories import KnowledgeDocumentRepository

class FakeCollection:
    def __init__(self):
        self.pipeline = None

    def aggregate(self, pipeline):
        self.pipeline = pipeline

        return [
            {
                "source_id": "source_001::chunk::0",
                "title": "Skin irritation guidance",
                "content": "General skin irritation information.",
                "source_type": "clinical_guideline",
                "url": "https://example.com/skin-guidance",
                "tags": ["irritation"],
                "metadata": {},
                "embedding": [0.1, 0.2, 0.3],
                "score": 0.91,
            }
        ]

def test_similarity_search_returns_documents_and_scores():
    collection = FakeCollection()
    repository = KnowledgeDocumentRepository(collection)

    results = repository.similarity_search(
        query_embedding=[0.1, 0.2, 0.3],
        limit=2,
    )

    assert len(results) == 1
    assert results[0]["document"].source_id == (
        "source_001::chunk::0"
    )
    assert results[0]["score"] == 0.91

def test_similarity_search_builds_vector_search_pipeline():
    collection = FakeCollection()
    repository = KnowledgeDocumentRepository(collection)

    repository.similarity_search(
        query_embedding=[0.1, 0.2, 0.3],
        limit=2,
    )

    vector_search_stage = collection.pipeline[0]["$vectorSearch"]

    assert vector_search_stage["index"] == (
        "knowledge_vector_index"
    )
    assert vector_search_stage["path"] == "embedding"
    assert vector_search_stage["queryVector"] == [
        0.1,
        0.2,
        0.3,
    ]
    assert vector_search_stage["limit"] == 2
    assert vector_search_stage["numCandidates"] >= 2