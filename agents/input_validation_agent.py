from agents.state import ConsultationState

def validate_input(state: ConsultationState) -> ConsultationState:
    """Validate that a consultation contains at least one input."""
    updated_state = dict(state)
    errors = list(state.get("errors", []))

    has_transcript = bool(state.get("transcript", "").strip())
    has_media = any(
        state.get(field_name)
        for field_name in (
            "audio_path",
            "image_path",
            "video_path",
        )
    )

    if not has_transcript and not has_media:
        message = "At least one consultation input is required."

        if message not in errors:
            errors.append(message)

    updated_state["errors"] = errors

    return updated_state