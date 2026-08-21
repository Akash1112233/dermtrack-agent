from agents.state import create_initial_state

def test_initial_state_contains_required_consultation_fields():
    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )

    assert state["patient_id"] == "patient_001"
    assert state["consultation_id"] == "consultation_001"
    assert state["transcript"] == ""
    assert state["image_observations"] == []
    assert state["retrieved_sources"] == []
    assert state["patient_history"] == []
    assert state["response_text"] == ""
    assert state["errors"] == []

def test_initial_state_media_fields_are_empty():
    state = create_initial_state(
        patient_id="patient_001",
        consultation_id="consultation_001",
    )

    assert state["audio_path"] is None
    assert state["image_path"] is None
    assert state["video_path"] is None
    assert state["audio_response_path"] is None