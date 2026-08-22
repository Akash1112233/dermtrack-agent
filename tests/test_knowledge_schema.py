from datetime import datetime

import pytest
from pydantic import ValidationError

from database.schemas import KnowledgeDocument

def test_knowledge_document_accepts_valid_data():
    document = KnowledgeDocument(
        source_id="source_001",
        title="General skin irritation guidance",
        content="General information about common skin irritation.",
        source_type="clinical_guideline",
        url="https://example.com/skin-guidance",
        tags=["irritation", "skin-care"],
    )

    assert document.source_id == "source_001"
    assert document.title == "General skin irritation guidance"
    assert document.source_type == "clinical_guideline"
    assert document.tags == ["irritation", "skin-care"]
    assert isinstance(document.created_at, datetime)

def test_knowledge_document_defaults_embedding_to_empty_list():
    document = KnowledgeDocument(
        source_id="source_002",
        title="Basic skin-care information",
        content="General skin-care information.",
        source_type="educational",
        url="https://example.com/basic-skin-care",
    )

    assert document.embedding == []
    assert document.tags == []

def test_knowledge_document_rejects_empty_content():
    with pytest.raises(ValidationError):
        KnowledgeDocument(
            source_id="source_003",
            title="Invalid document",
            content="",
            source_type="educational",
            url="https://example.com/invalid",
        )

def test_knowledge_document_accepts_embedding():
    document = KnowledgeDocument(
        source_id="source_004",
        title="Embedded document",
        content="Document with an embedding.",
        source_type="clinical_guideline",
        url="https://example.com/embedded",
        embedding=[0.12, 0.45, 0.89],
    )

    assert document.embedding == [0.12, 0.45, 0.89]