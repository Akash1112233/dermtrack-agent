import hashlib
from typing import Any

from database.schemas import RetrievedSource


def build_safe_research_query(state: dict[str, Any]) -> str:
    """Build a de-identified query from structured observations only."""
    intake = state.get("patient_intake") or {}
    if hasattr(intake, "model_dump"):
        intake = intake.model_dump()
    parts = [
        str(intake.get("symptom_duration", "")),
        str(intake.get("progression", "")),
        str(intake.get("affected_area", "")),
        str(intake.get("triggers", "")),
    ]
    observations = state.get("image_observations", [])
    parts.extend(
        observation.feature
        for observation in observations
        if getattr(observation, "feature", "")
    )
    terms = [part.strip() for part in parts if part.strip()]
    return "general dermatology safety guidance " + " ".join(terms)


def web_research_node(state: dict[str, Any], tavily_service: Any | None) -> dict[str, Any]:
    """Run bounded web research without sending raw patient text or identifiers."""
    updated_state = dict(state)
    mode = state.get("research_mode", "auto")
    local_sources = state.get("retrieved_sources", [])
    if tavily_service is None or mode == "local_only":
        return updated_state
    if mode == "auto" and local_sources:
        return updated_state

    query = build_safe_research_query(state)
    try:
        results = tavily_service.search(query)
    except Exception as error:
        errors = list(state.get("errors", []))
        errors.append(f"Web research unavailable: {error}")
        updated_state["errors"] = errors
        updated_state["web_retrieved_sources"] = []
        return updated_state

    sources = []
    for result in results:
        source_id = "web::" + hashlib.sha256(result.url.encode()).hexdigest()[:16]
        sources.append(
            RetrievedSource(
                source_id=source_id,
                title=result.title,
                url=result.url,
                similarity_score=max(0.0, min(1.0, result.score or 0.0)),
            )
        )
    updated_state["web_retrieved_sources"] = sources
    return updated_state
