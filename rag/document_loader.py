from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentPage:
    """Extracted source content with its original page number."""

    text: str
    page_number: int


def load_document(path: str | Path) -> list[DocumentPage]:
    """Load UTF-8 text/Markdown or a PDF into page-aware text records."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    suffix = source_path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        text = source_path.read_text(encoding="utf-8").strip()
        return [DocumentPage(text=text, page_number=1)] if text else []

    if suffix != ".pdf":
        raise ValueError("Supported source formats are .txt, .md, .markdown, and .pdf.")

    import fitz

    pages: list[DocumentPage] = []
    with fitz.open(source_path) as pdf:
        for index, page in enumerate(pdf):
            text = page.get_text("text").strip()
            if text:
                pages.append(DocumentPage(text=text, page_number=index + 1))
    return pages
