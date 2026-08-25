from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.input_validation_agent import validate_input
from agents.nodes.web_researcher import web_research_node
from agents.state import ConsultationState
from database.schemas import Consultation
from services.gemini_vision import GeminiVisionService
from services.groq_service import GroqTranscriptionService
from services.triage_service import SafetyTriageService


def build_consultation_graph(
    transcription_service: Any | None = None,
    vision_service: Any | None = None,
    triage_service: Any | None = None,
    retrieval_service: Any | None = None,
    response_service: Any | None = None,
    consultation_repository: Any | None = None,
    tavily_service: Any | None = None,
):
    """Build and compile the consultation LangGraph workflow."""
    transcription = transcription_service
    vision = vision_service
    triage = triage_service or SafetyTriageService()
    retrieval = retrieval_service
    response = response_service
    repository = consultation_repository

    def transcription_node(state: ConsultationState) -> ConsultationState:
        updated_state = dict(state)
        audio_path = state.get("audio_path")
        if not audio_path:
            return updated_state
        if transcription is None:
            errors = list(state.get("errors", []))
            errors.append("Transcription service is not configured.")
            updated_state["errors"] = errors
            return updated_state
        updated_state["transcript"] = transcription.transcribe(audio_path)
        return updated_state

    def vision_node(state: ConsultationState) -> ConsultationState:
        updated_state = dict(state)
        image_path = state.get("image_path")
        if not image_path:
            return updated_state
        if vision is None:
            errors = list(state.get("errors", []))
            errors.append("Vision service is not configured.")
            updated_state["errors"] = errors
            return updated_state
        updated_state["image_observations"] = vision.analyze_image(image_path)
        return updated_state

    def triage_node(state: ConsultationState) -> ConsultationState:
        updated_state = dict(state)
        updated_state["triage"] = triage.evaluate(
            transcript=state.get("transcript", ""),
            observations=state.get("image_observations", []),
        )
        return updated_state

    def retrieval_node(state: ConsultationState) -> ConsultationState:
        updated_state = dict(state)
        query = state.get("transcript", "").strip()
        if not query:
            query = " ".join(
                observation.feature
                for observation in state.get("image_observations", [])
            ).strip()
        if not query or retrieval is None:
            return updated_state
        updated_state["retrieved_sources"] = retrieval.retrieve(query=query, limit=4)
        return updated_state

    def web_research(state: ConsultationState) -> ConsultationState:
        return web_research_node(state, tavily_service)

    def response_node(state: ConsultationState) -> ConsultationState:
        updated_state = dict(state)
        if response is None:
            return updated_state
        sources = list(state.get("retrieved_sources", []))
        sources.extend(state.get("web_retrieved_sources", []))
        updated_state["response_text"] = response.generate(
            transcript=state.get("transcript", ""),
            observations=state.get("image_observations", []),
            triage=state.get("triage"),
            sources=sources,
        )
        return updated_state

    def persistence_node(state: ConsultationState) -> ConsultationState:
        updated_state = dict(state)
        if repository is None:
            return updated_state
        triage_result = state.get("triage")
        response_text = state.get("response_text", "").strip()
        if triage_result is None or not response_text:
            return updated_state
        sources = list(state.get("retrieved_sources", []))
        sources.extend(state.get("web_retrieved_sources", []))
        consultation = Consultation(
            consultation_id=state["consultation_id"],
            patient_id=state["patient_id"],
            transcript=state.get("transcript", ""),
            patient_intake=state.get("patient_intake", {}),
            image_file_id=state.get("image_file_id"),
            image_content_type=state.get("image_content_type"),
            observations=state.get("image_observations", []),
            triage=triage_result,
            retrieved_sources=sources,
            response_text=response_text,
        )
        repository.create(consultation)
        return updated_state

    builder = StateGraph(ConsultationState)
    builder.add_node("validate_input", validate_input)
    builder.add_node("transcription", transcription_node)
    builder.add_node("vision_analysis", vision_node)
    builder.add_node("safety_triage", triage_node)
    builder.add_node("rag_retrieval", retrieval_node)
    builder.add_node("web_research", web_research)
    builder.add_node("response_generation", response_node)
    builder.add_node("persistence", persistence_node)

    builder.add_edge(START, "validate_input")
    builder.add_edge("validate_input", "transcription")
    builder.add_edge("transcription", "vision_analysis")
    builder.add_edge("vision_analysis", "safety_triage")
    builder.add_edge("safety_triage", "rag_retrieval")
    builder.add_edge("rag_retrieval", "web_research")
    builder.add_edge("web_research", "response_generation")
    builder.add_edge("response_generation", "persistence")
    builder.add_edge("persistence", END)
    return builder.compile()
