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

class FakeMultimodalApplication:
    def __init__(self):
        self.received_state = None

    def run(self, state):
        self.received_state = state

        return {
            **state,
            "triage": SimpleNamespace(
                risk_level="low",
                needs_human_review=False,
            ),
            "response_text": (
                "Image analysis completed safely."
            ),
            "retrieved_sources": [],
            "errors": [],
        }
def test_multimodal_consultation_accepts_image_upload():
    fake_application = FakeMultimodalApplication()
    app = create_app(application=fake_application)
    client = TestClient(app)

    response = client.post(
        "/consultations/multimodal",
        data={
            "patient_id": "patient_001",
            "transcript": (
                "I have mild redness on my cheek."
            ),
        },
        files={
            "image": (
                "skin.png",
                b"synthetic-image-content",
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["patient_id"] == "patient_001"
    assert body["risk_level"] == "low"
    assert body["response_text"] == (
        "Image analysis completed safely."
    )

    assert fake_application.received_state is not None
    assert fake_application.received_state["image_path"]


class FakeHistoryRepository:
    def __init__(self):
        self.patient_id = None
        self.limit = None

    def list_by_patient(self, patient_id, limit=20):
        self.patient_id = patient_id
        self.limit = limit
        return []


class FakeHistoryApplication(FakeApplication):
    def __init__(self):
        self.consultation_repository = FakeHistoryRepository()


def test_get_patient_consultations_returns_history():
    fake_application = FakeHistoryApplication()
    app = create_app(application=fake_application)
    client = TestClient(app)

    response = client.get(
        "/patients/patient_001/consultations?limit=10"
    )

    assert response.status_code == 200
    assert response.json() == []
    assert (
        fake_application.consultation_repository.patient_id
        == "patient_001"
    )
    assert fake_application.consultation_repository.limit == 10


def test_demo_ui_is_available():
    app = create_app(application=FakeApplication())
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "DermTrack Agent" in response.text
    assert "consultation-form" in response.text


class FakeDeepgramService:
    def __init__(self):
        self.received_audio = None
        self.received_text = None

    def transcribe_bytes(self, audio_bytes, content_type):
        self.received_audio = (audio_bytes, content_type)
        return "I have itching and redness."

    def synthesize(self, text):
        self.received_text = text
        return b"fake-mp3-audio"


class FakeAudioApplication(FakeApplication):
    def __init__(self):
        self.deepgram_service = FakeDeepgramService()


def test_transcribe_endpoint_uses_deepgram():
    fake_application = FakeAudioApplication()
    app = create_app(application=fake_application)
    client = TestClient(app)

    response = client.post(
        "/transcribe",
        files={
            "audio": (
                "recording.webm",
                b"fake-audio",
                "audio/webm",
            )
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "transcript": "I have itching and redness."
    }
    assert fake_application.deepgram_service.received_audio == (
        b"fake-audio",
        "audio/webm",
    )


def test_speak_endpoint_returns_audio():
    fake_application = FakeAudioApplication()
    app = create_app(application=fake_application)
    client = TestClient(app)

    response = client.post(
        "/speak",
        data={"text": "Please contact a clinician."},
    )

    assert response.status_code == 200
    assert response.content == b"fake-mp3-audio"
    assert response.headers["content-type"] == "audio/mpeg"
