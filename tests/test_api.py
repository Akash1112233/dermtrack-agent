from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import create_app

class FakeApplication:
    def run(self, state):
        return {
            **state,
            "triage": SimpleNamespace(
                risk_level="low",
                needs_human_review=False,
            ),
            "response_text": (
                "This is educational information, "
                "not a diagnosis."
            ),
            "retrieved_sources": [],
            "errors": [],
        }

def test_create_consultation_returns_response():
    app = create_app(application=FakeApplication())
    client = TestClient(app)

    response = client.post(
        "/consultations",
        json={
            "patient_id": "patient_001",
            "transcript": "I have mild redness on my cheek.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["patient_id"] == "patient_001"
    assert body["risk_level"] == "low"
    assert body["response_text"].strip() != ""
    assert body["consultation_id"].strip() != ""

def test_create_consultation_rejects_empty_transcript():
    app = create_app(application=FakeApplication())
    client = TestClient(app)

    response = client.post(
        "/consultations",
        json={
            "patient_id": "patient_001",
            "transcript": "   ",
        },
    )

    assert response.status_code == 422