from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentChunker:
    """Split knowledge documents into retrieval-friendly chunks."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def split(self, text: str) -> list[str]:
        """Split text into cleaned chunks."""
        if not text.strip():
            return []

        return [
            chunk.strip()
            for chunk in self.splitter.split_text(text)
            if chunk.strip()
        ]