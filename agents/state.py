from typing import TypedDict

from database.schemas import (
    Consultation,
    ImageObservation,
    PatientIntake,
    RetrievedSource,
    TriageResult,
)


class ConsultationState(TypedDict, total=False):
    """Shared state passed through the LangGraph workflow."""

    patient_id: str
    consultation_id: str
    audio_path: str | None
    image_path: str | None
    image_file_id: str | None
    image_content_type: str | None
    video_path: str | None
    transcript: str
    patient_intake: PatientIntake
    image_observations: list[ImageObservation]
    triage: TriageResult | None
    retrieved_sources: list[RetrievedSource]
    patient_history: list[Consultation]
    response_text: str
    audio_response_path: str | None
    errors: list[str]


def create_initial_state(
    patient_id: str,
    consultation_id: str,
    patient_intake: PatientIntake | None = None,
) -> ConsultationState:
    """Create an empty state for a new consultation."""
    return ConsultationState(
        patient_id=patient_id,
        consultation_id=consultation_id,
        audio_path=None,
        image_path=None,
        image_file_id=None,
        image_content_type=None,
        video_path=None,
        transcript="",
        patient_intake=patient_intake or PatientIntake(),
        image_observations=[],
        triage=None,
        retrieved_sources=[],
        patient_history=[],
        response_text="",
        audio_response_path=None,
        errors=[],
    )
