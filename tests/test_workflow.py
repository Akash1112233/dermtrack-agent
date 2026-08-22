from database.schemas import ImageObservation
from agents.state import create_initial_state
from agents.workflow import build_consultation_graph
from services.triage_service import SafetyTriageService
from database.schemas import ImageObservation, RetrievedSource

class FakeTranscriptionService:
    def transcribe(self, audio_path):
        return "I have redness on my cheek."

class FakeVisionService:
    def analyze_image(self, image_path):
        return [
            ImageObservation(
                feature="localized redness",
                confidence=0.86,
                body_area="left cheek",
            )
        ]

def test_workflow_processes_audio_image_and_triage():
    graph = build_consultation_graph(
        transcription_service=FakeTranscriptionService(),
        vision_service=FakeVisionService(),
        triage_service=SafetyTriageService(),
    )

    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["audio_path"] = "data/demo/patient.wav"
    state["image_path"] = "data/demo/skin.jpg"

    result = graph.invoke(state)

    assert result["transcript"] == "I have redness on my cheek."
    assert len(result["image_observations"]) == 1
    assert result["image_observations"][0].feature == "localized redness"
    assert result["triage"].risk_level == "low"
    assert result["errors"] == []

def test_workflow_rejects_empty_consultation():
    graph = build_consultation_graph(
        transcription_service=FakeTranscriptionService(),
        vision_service=FakeVisionService(),
        triage_service=SafetyTriageService(),
    )

    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )

    result = graph.invoke(state)

    assert len(result["errors"]) == 1
    assert "At least one consultation input is required" in result["errors"][0]


class FakeRetrievalService:
    def retrieve(self, query, limit=4):
        assert "redness" in query.lower()
        assert limit == 4

        return [
            RetrievedSource(
                source_id="source_001::chunk::0",
                title="Skin irritation guidance",
                url="https://example.com/skin-guidance",
                similarity_score=0.90,
            )
        ]
    
def test_workflow_adds_retrieved_sources():
    graph = build_consultation_graph(
        transcription_service=FakeTranscriptionService(),
        vision_service=FakeVisionService(),
        triage_service=SafetyTriageService(),
        retrieval_service=FakeRetrievalService(),
    )

    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["audio_path"] = "data/demo/patient.wav"

    result = graph.invoke(state)

    assert len(result["retrieved_sources"]) == 1
    assert result["retrieved_sources"][0].source_id == (
        "source_001::chunk::0"
    )

class FakeResponseService:
    def generate(
        self,
        transcript,
        observations,
        triage,
        sources,
    ):
        assert transcript == "I have redness on my cheek."
        assert len(observations) == 1
        assert triage.risk_level == "low"

        return (
            "Your description includes localized redness. "
            "This is educational information, not a diagnosis."
        )

def test_workflow_generates_response_text():
    graph = build_consultation_graph(
        transcription_service=FakeTranscriptionService(),
        vision_service=FakeVisionService(),
        triage_service=SafetyTriageService(),
        response_service=FakeResponseService(),
    )

    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["audio_path"] = "data/demo/patient.wav"
    state["image_path"] = "data/demo/skin.jpg"

    result = graph.invoke(state)

    assert "localized redness" in result["response_text"]
    assert result["response_text"].strip() != ""

class FakeConsultationRepository:
    def __init__(self):
        self.saved_consultations = []

    def create(self, consultation):
        self.saved_consultations.append(consultation)
        return consultation

def test_workflow_persists_completed_consultation():
    consultation_repository = FakeConsultationRepository()

    graph = build_consultation_graph(
        transcription_service=FakeTranscriptionService(),
        vision_service=FakeVisionService(),
        triage_service=SafetyTriageService(),
        response_service=FakeResponseService(),
        consultation_repository=consultation_repository,
    )

    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["audio_path"] = "data/demo/patient.wav"
    state["image_path"] = "data/demo/skin.jpg"

    result = graph.invoke(state)

    assert len(consultation_repository.saved_consultations) == 1

    saved_consultation = (
        consultation_repository.saved_consultations[0]
    )

    assert saved_consultation.consultation_id == (
        "consultation_001"
    )
    assert saved_consultation.patient_id == "patient_001"
    assert saved_consultation.transcript == (
        "I have redness on my cheek."
    )
    assert saved_consultation.triage.risk_level == "low"
    assert saved_consultation.response_text.strip() != ""