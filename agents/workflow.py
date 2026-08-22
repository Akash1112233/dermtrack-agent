from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.input_validation_agent import validate_input
from agents.state import ConsultationState
from services.gemini_vision import GeminiVisionService
from services.groq_service import GroqTranscriptionService
from services.triage_service import SafetyTriageService

def build_consultation_graph(
    transcription_service: Any | None = None,
    vision_service: Any | None = None,
    triage_service: Any | None = None,
):
    """Build and compile the consultation LangGraph workflow."""

    transcription = transcription_service
    vision = vision_service
    triage = triage_service or SafetyTriageService()

    def transcription_node(
        state: ConsultationState,
    ) -> ConsultationState:
        updated_state = dict(state)

        audio_path = state.get("audio_path")

        if not audio_path:
            return updated_state

        if transcription is None:
            errors = list(state.get("errors", []))
            errors.append(
                "Transcription service is not configured."
            )
            updated_state["errors"] = errors
            return updated_state

        updated_state["transcript"] = transcription.transcribe(
            audio_path
        )
        return updated_state

    def vision_node(
        state: ConsultationState,
    ) -> ConsultationState:
        updated_state = dict(state)

        image_path = state.get("image_path")

        if not image_path:
            return updated_state

        if vision is None:
            errors = list(state.get("errors", []))
            errors.append(
                "Vision service is not configured."
            )
            updated_state["errors"] = errors
            return updated_state

        updated_state["image_observations"] = vision.analyze_image(
            image_path
        )
        return updated_state

    def triage_node(
        state: ConsultationState,
    ) -> ConsultationState:
        updated_state = dict(state)

        updated_state["triage"] = triage.evaluate(
            transcript=state.get("transcript", ""),
            observations=state.get("image_observations", []),
        )

        return updated_state

    builder = StateGraph(ConsultationState)

    builder.add_node("validate_input", validate_input)
    builder.add_node("transcription", transcription_node)
    builder.add_node("vision_analysis", vision_node)
    builder.add_node("safety_triage", triage_node)

    builder.add_edge(START, "validate_input")
    builder.add_edge("validate_input", "transcription")
    builder.add_edge("transcription", "vision_analysis")
    builder.add_edge("vision_analysis", "safety_triage")
    builder.add_edge("safety_triage", END)

    return builder.compile()