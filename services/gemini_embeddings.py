from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings

class GeminiEmbeddingService:
    """Create vector embeddings using Gemini."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-embedding-001",
        embeddings: Any | None = None,
    ):
        self.embeddings = embeddings or GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=api_key,
        )

    def embed_text(self, text: str) -> list[float]:
        """Embed one text value."""
        if not text.strip():
            raise ValueError("text cannot be empty.")

        embedding = self.embeddings.embed_query(text)

        return [float(value) for value in embedding]

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        """Embed multiple document chunks."""
        if not documents:
            raise ValueError("documents cannot be empty.")

        if any(not document.strip() for document in documents):
            raise ValueError(
                "documents cannot contain empty text."
            )

        embeddings = self.embeddings.embed_documents(documents)

        return [
            [float(value) for value in embedding]
            for embedding in embeddings
        ]