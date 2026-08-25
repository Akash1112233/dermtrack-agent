from dataclasses import dataclass
from typing import Any, Protocol


class TavilyClient(Protocol):
    def post(self, url: str, *, json: dict[str, Any], timeout: float) -> Any:
        ...


class TavilyServiceError(RuntimeError):
    """A recoverable Tavily provider failure."""


@dataclass(frozen=True)
class TavilyResult:
    title: str
    url: str
    content: str
    score: float | None = None
    published_date: str | None = None


class TavilyService:
    """Bounded, injectable Tavily search service."""

    def __init__(
        self,
        api_key: str | None,
        api_url: str = "https://api.tavily.com/search",
        allowed_domains: list[str] | None = None,
        max_results: int = 5,
        timeout_seconds: float = 10.0,
        client: TavilyClient | None = None,
    ):
        if max_results <= 0 or max_results > 10:
            raise ValueError("max_results must be between 1 and 10.")
        self.api_key = api_key
        self.api_url = api_url
        self.allowed_domains = allowed_domains or []
        self.max_results = max_results
        self.timeout_seconds = timeout_seconds
        if client is None:
            import httpx

            client = httpx.Client()
        self.client = client

    def search(
        self,
        query: str,
        *,
        domains: list[str] | None = None,
        max_results: int | None = None,
    ) -> list[TavilyResult]:
        if not query.strip():
            raise ValueError("query cannot be empty.")
        if not self.api_key:
            raise TavilyServiceError("Tavily is not configured.")

        requested_domains = domains or self.allowed_domains
        payload: dict[str, Any] = {
            "api_key": self.api_key,
            "query": query.strip(),
            "search_depth": "advanced",
            "max_results": max_results or self.max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        if requested_domains:
            payload["include_domains"] = requested_domains

        try:
            response = self.client.post(
                self.api_url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except Exception as error:
            raise TavilyServiceError("Tavily search failed.") from error

        results = []
        for item in body.get("results", []):
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            content = str(item.get("content", "")).strip()
            if not url or not title or not content:
                continue
            results.append(
                TavilyResult(
                    title=title,
                    url=url,
                    content=content,
                    score=float(item["score"]) if item.get("score") is not None else None,
                    published_date=item.get("published_date"),
                )
            )
        return results
