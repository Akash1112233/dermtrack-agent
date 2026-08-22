from uuid import uuid4
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator
from agents.state import create_initial_state
from app.application import ConsultationApplication

class ConsultationRequest(BaseModel):
    """Request body for a text consultation."""

    patient_id: str = Field(min_length=1)
    transcript: str = Field(min_length=1)

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "transcript must contain non-whitespace text."
            )

        return cleaned_value

class ConsultationResponse(BaseModel):
    """API response for a completed consultation."""

    consultation_id: str
    patient_id: str
    risk_level: str
    needs_human_review: bool
    response_text: str
    retrieved_sources: list[dict[str, Any]]

def create_app(
    application: Any | None = None,
) -> FastAPI:
    """Create the DermTrack FastAPI application."""
    configured_application = (
        application or ConsultationApplication()
    )

    app = FastAPI(
        title="DermTrack Agent API",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/consultations",
        response_model=ConsultationResponse,
    )
    def create_consultation(
        request: ConsultationRequest,
    ) -> ConsultationResponse:
        consultation_id = f"consultation_{uuid4().hex}"

        state = create_initial_state(
            patient_id=request.patient_id,
            consultation_id=consultation_id,
        )
        state["transcript"] = request.transcript

        result = configured_application.run(state)

        triage = result.get("triage")

        if triage is None:
            raise ValueError(
                "The workflow did not produce a triage result."
            )

        sources = [
            source.model_dump(mode="json")
            for source in result.get(
                "retrieved_sources",
                [],
            )
        ]

        return ConsultationResponse(
            consultation_id=consultation_id,
            patient_id=request.patient_id,
            risk_level=triage.risk_level,
            needs_human_review=triage.needs_human_review,
            response_text=result.get("response_text", ""),
            retrieved_sources=sources,
        )

    return app