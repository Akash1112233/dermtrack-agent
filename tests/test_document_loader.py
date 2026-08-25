from pathlib import Path

import fitz
import pytest

from rag.document_loader import DocumentPage, load_document


def test_load_document_reads_markdown_as_one_page(tmp_path: Path):
    source = tmp_path / "guidance.md"
    source.write_text("# Guidance\n\nTrusted content.", encoding="utf-8")

    pages = load_document(source)

    assert pages == [DocumentPage(text="# Guidance\n\nTrusted content.", page_number=1)]


def test_load_document_reads_pdf_page_text(tmp_path: Path):
    source = tmp_path / "guidance.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Page one guidance")
        pdf.save(source)

    pages = load_document(source)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Page one guidance" in pages[0].text


def test_load_document_rejects_unsupported_format(tmp_path: Path):
    source = tmp_path / "guidance.docx"
    source.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="Supported source formats"):
        load_document(source)
