from agents.state import create_initial_state
from app.application import ConsultationApplication

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
    def generate(
        self,
        transcript,
        observations,
        triage,
        sources,
    ):
        return "Educational response."

class FakeConsultationRepository:
    def create(self, consultation):
        return consultation

class FakeRepositories:
    consultations = FakeConsultationRepository()

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