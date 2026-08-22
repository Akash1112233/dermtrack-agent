from database.schemas import ImageObservation
from agents.state import create_initial_state
from agents.workflow import build_consultation_graph
from services.triage_service import SafetyTriageService

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