from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from database.schemas import (
    Consultation,
    ImageObservation,
    Patient,
    RetrievedSource,
    TriageResult,
)

def test_patient_schema_accepts_valid_patient():
    patient = Patient(
        patient_id="patient_001",
        consent_for_storage=True,
    )

    assert patient.patient_id == "patient_001"
    assert patient.consent_for_storage is True
    assert isinstance(patient.created_at, datetime)

def test_image_observation_accepts_valid_observation():
    observation = ImageObservation(
        feature="localized redness",
        confidence=0.82,
        body_area="left cheek",
    )

    assert observation.feature == "localized redness"
    assert observation.confidence == 0.82
    assert observation.body_area == "left cheek"

def test_triage_schema_accepts_valid_risk_level():
    triage = TriageResult(
        risk_level="low",
        red_flags=[],
        needs_human_review=False,
        explanation="No urgent warning signs were identified.",
    )

    assert triage.risk_level == "low"
    assert triage.needs_human_review is False

def test_triage_schema_rejects_invalid_risk_level():
    with pytest.raises(ValidationError):
        TriageResult(
            risk_level="unknown-risk",
            red_flags=[],
            needs_human_review=False,
            explanation="Invalid risk level.",
        )

def test_consultation_schema_contains_required_information():
    consultation = Consultation(
        consultation_id="consultation_001",
        patient_id="patient_001",
        transcript="I have redness on my cheek.",
        observations=[
            ImageObservation(
                feature="localized redness",
                confidence=0.76,
                body_area="left cheek",
            )
        ],
        triage=TriageResult(
            risk_level="low",
            red_flags=[],
            needs_human_review=False,
            explanation="No urgent warning signs were identified.",
        ),
        retrieved_sources=[
            RetrievedSource(
                source_id="source_001",
                title="General skin irritation guidance",
                url="https://example.com/skin-irritation",
                similarity_score=0.88,
            )
        ],
        response_text="This is general informational guidance.",
    )

    assert consultation.consultation_id == "consultation_001"
    assert consultation.patient_id == "patient_001"
    assert len(consultation.observations) == 1
    assert len(consultation.retrieved_sources) == 1
    assert consultation.triage.risk_level == "low"
    assert consultation.created_at.tzinfo == timezone.utc