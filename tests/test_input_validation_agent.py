from agents.input_validation_agent import validate_input
from agents.state import create_initial_state

def test_validation_accepts_transcript_input():
    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["transcript"] = "I have redness on my cheek."

    result = validate_input(state)

    assert result["errors"] == []

def test_validation_accepts_image_input():
    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["image_path"] = "data/demo/skin-image.jpg"

    result = validate_input(state)

    assert result["errors"] == []

def test_validation_rejects_empty_consultation():
    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )

    result = validate_input(state)

    assert len(result["errors"]) == 1
    assert "At least one consultation input is required" in result["errors"][0]

def test_validation_preserves_existing_state():
    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )
    state["transcript"] = "I have itching."
    state["image_path"] = "data/demo/skin-image.jpg"

    result = validate_input(state)

    assert result["patient_id"] == "patient_001"
    assert result["consultation_id"] == "consultation_001"
    assert result["transcript"] == "I have itching."
    assert result["image_path"] == "data/demo/skin-image.jpg"