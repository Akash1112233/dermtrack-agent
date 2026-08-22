from types import SimpleNamespace

import pytest

from database.schemas import (
    ImageObservation,
    RetrievedSource,
    TriageResult,
)
from services.gemini_response import GeminiResponseService

class FakeChatModel:
    def __init__(self):
        self.received_messages = None

    def invoke(self, messages):
        self.received_messages = messages

        return SimpleNamespace(
            content=(
                "Your description includes redness. "
                "This information is educational and not a diagnosis."
            )
        )

def test_response_service_generates_patient_response():
    fake_model = FakeChatModel()

    service = GeminiResponseService(
        api_key="test-key",
        model_name="gemini-2.5-flash",
        model=fake_model,
    )

    response = service.generate(
        transcript="I have redness on my cheek.",
        observations=[
            ImageObservation(
                feature="localized redness",
                confidence=0.85,
                body_area="left cheek",
            )
        ],
        triage=TriageResult(
            risk_level="low",
            red_flags=[],
            needs_human_review=False,
            explanation="No urgent warning signs were identified.",
        ),
        sources=[
            RetrievedSource(
                source_id="source_001",
                title="Skin-care guidance",
                url="https://example.com/skin-guidance",
                similarity_score=0.90,
            )
        ],
    )

    assert "redness" in response.lower()
    assert fake_model.received_messages is not None

def test_response_service_rejects_empty_consultation():
    service = GeminiResponseService(
        api_key="test-key",
        model_name="gemini-2.5-flash",
        model=FakeChatModel(),
    )

    with pytest.raises(ValueError, match="consultation data"):
        service.generate(
            transcript="",
            observations=[],
            triage=None,
            sources=[],
        )

class StructuredFakeChatModel:
    def invoke(self, messages):
        return SimpleNamespace(
            content=[
                {
                    "type": "text",
                    "text": "Structured Gemini response.",
                }
            ]
        )
def test_response_service_handles_structured_content():
    service = GeminiResponseService(
        api_key="test-key",
        model_name="gemini-3.6-flash",
        model=StructuredFakeChatModel(),
    )

    response = service.generate(
        transcript="I have mild redness.",
        observations=[],
        triage=None,
        sources=[],
    )

    assert response == "Structured Gemini response."