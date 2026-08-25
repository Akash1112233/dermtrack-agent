import pytest

from services.tavily_service import TavilyService, TavilyServiceError


class FakeResponse:
    def __init__(self, body, error=None):
        self.body = body
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.body


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, *, json, timeout):
        self.calls.append((url, json, timeout))
        return self.response


def test_tavily_search_sends_bounded_allowlisted_request():
    client = FakeClient(FakeResponse({
        "results": [{
            "title": "Trusted source",
            "url": "https://aad.org/skin",
            "content": "Educational content",
            "score": 0.91,
            "published_date": "2026-01-01",
        }]
    }))
    service = TavilyService(
        api_key="test-key",
        allowed_domains=["aad.org"],
        max_results=3,
        client=client,
    )

    results = service.search("general skin safety guidance")

    assert results[0].url == "https://aad.org/skin"
    assert client.calls[0][1]["max_results"] == 3
    assert client.calls[0][1]["include_domains"] == ["aad.org"]
    assert client.calls[0][1]["api_key"] == "test-key"


def test_tavily_rejects_missing_key_without_calling_provider():
    service = TavilyService(api_key=None, client=FakeClient(FakeResponse({})))

    with pytest.raises(TavilyServiceError, match="not configured"):
        service.search("skin guidance")


def test_tavily_wraps_provider_failures():
    client = FakeClient(FakeResponse({}, error=RuntimeError("quota")))
    service = TavilyService(api_key="test-key", client=client)

    with pytest.raises(TavilyServiceError, match="search failed"):
        service.search("skin guidance")


def test_tavily_rejects_empty_query():
    service = TavilyService(api_key="test-key", client=FakeClient(FakeResponse({})))

    with pytest.raises(ValueError, match="query"):
        service.search(" ")
