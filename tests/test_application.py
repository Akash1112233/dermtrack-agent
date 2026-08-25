from agents.state import create_initial_state
from app.application import ConsultationApplication
from app.config import Settings


class FakeTranscriptionService:
    def transcribe(self, audio_path):
        return "I have redness on my cheek."


class FakeVisionService:
    def analyze_image(self, image_path):
        return []


class FakeRetrievalService:
    def retrieve(self, query, limit=4):
        return []


class FakeResponseService:
    def generate(self, transcript, observations, triage, sources):
        return "Educational response."


class FakeConsultationRepository:
    def create(self, consultation):
        return consultation


class FakeRepositories:
    consultations = FakeConsultationRepository()
    knowledge_documents = object()


def test_application_builds_and_runs_workflow():
    application = ConsultationApplication(
        repositories=FakeRepositories(),
        transcription_service=FakeTranscriptionService(),
        vision_service=FakeVisionService(),
        retrieval_service=FakeRetrievalService(),
        response_service=FakeResponseService(),
    )

    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["audio_path"] = "data/demo/patient.wav"

    result = application.run(state)

    assert result["transcript"] == "I have redness on my cheek."
    assert result["response_text"] == "Educational response."
    assert result["triage"].risk_level == "low"


def test_application_selects_chroma_backend(monkeypatch, tmp_path):
    calls = []

    class FakeChromaVectorStore:
        def __init__(self, persist_directory, collection_name):
            calls.append((persist_directory, collection_name))

    monkeypatch.setattr("app.application.ChromaVectorStore", FakeChromaVectorStore)
    settings = Settings(
        groq_api_key="test-groq",
        google_api_key="test-google",
        deepgram_api_key="test-deepgram",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_database="dermtrack",
        vector_store_backend="chroma",
        chroma_persist_directory=str(tmp_path / "chroma"),
        chroma_collection_name="test-knowledge",
    )

    ConsultationApplication(
        settings=settings,
        repositories=FakeRepositories(),
        transcription_service=FakeTranscriptionService(),
        vision_service=FakeVisionService(),
        response_service=FakeResponseService(),
    )

    assert calls == [(str(tmp_path / "chroma"), "test-knowledge")]
