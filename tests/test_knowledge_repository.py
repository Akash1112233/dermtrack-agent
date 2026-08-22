from database.repositories import KnowledgeDocumentRepository
from database.schemas import KnowledgeDocument

class FakeCollection:
    def __init__(self):
        self.documents = {}

    def replace_one(self, query, document, upsert=False):
        assert upsert is True
        source_id = query["source_id"]
        self.documents[source_id] = document

    def find_one(self, query):
        return self.documents.get(query["source_id"])

def make_document():
    return KnowledgeDocument(
        source_id="source_001",
        title="General skin irritation guidance",
        content="General information about common skin irritation.",
        source_type="clinical_guideline",
        url="https://example.com/skin-guidance",
        tags=["irritation", "skin-care"],
    )

def test_knowledge_repository_upserts_document():
    collection = FakeCollection()
    repository = KnowledgeDocumentRepository(collection)
    document = make_document()

    saved_document = repository.upsert(document)

    assert saved_document.source_id == "source_001"
    assert collection.documents["source_001"]["title"] == (
        "General skin irritation guidance"
    )

def test_knowledge_repository_retrieves_document():
    collection = FakeCollection()
    repository = KnowledgeDocumentRepository(collection)
    document = make_document()

    repository.upsert(document)
    retrieved_document = repository.get_by_source_id("source_001")

    assert retrieved_document is not None
    assert retrieved_document.source_id == "source_001"
    assert retrieved_document.content == (
        "General information about common skin irritation."
    )

def test_knowledge_repository_returns_none_for_unknown_source():
    collection = FakeCollection()
    repository = KnowledgeDocumentRepository(collection)

    result = repository.get_by_source_id("missing_source")

    assert result is None