import pytest

from rag.chunking import DocumentChunker

def test_chunker_splits_long_document():
    chunker = DocumentChunker(
        chunk_size=60,
        chunk_overlap=10,
    )

    text = (
        "Skin-care guidance should be based on trusted sources. "
        "Patients should monitor changes over time. "
        "Persistent or worsening symptoms may require professional review. "
        "This content is educational and is not a diagnosis."
    )

    chunks = chunker.split(text)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 60 for chunk in chunks)

def test_chunker_returns_empty_list_for_empty_text():
    chunker = DocumentChunker()

    assert chunker.split("") == []
    assert chunker.split("   ") == []

def test_chunker_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=100,
            chunk_overlap=100,
        )