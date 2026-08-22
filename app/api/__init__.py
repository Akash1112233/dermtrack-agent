from uuid import uuid4
from typing import Any
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pathlib import Path
from tempfile import NamedTemporaryFile
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

    @app.post(
        "/consultations/multimodal",
        response_model=ConsultationResponse,
    )
    async def create_multimodal_consultation(
        patient_id: str = Form(...),
        transcript: str = Form(""),
        image: UploadFile | None = File(default=None),
    ) -> ConsultationResponse:
        cleaned_patient_id = patient_id.strip()
        cleaned_transcript = transcript.strip()

        if not cleaned_patient_id:
            raise HTTPException(
                status_code=422,
                detail="patient_id cannot be empty.",
            )

        if not cleaned_transcript and image is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Provide a transcript or an image."
                ),
            )

        temporary_path: str | None = None

        try:
            state = create_initial_state(
                patient_id=cleaned_patient_id,
                consultation_id=(
                    f"consultation_{uuid4().hex}"
                ),
            )

            state["transcript"] = cleaned_transcript

            if image is not None:
                allowed_types = {
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                }

                if image.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=415,
                        detail=(
                            "Only JPEG, PNG, and WEBP "
                            "images are supported."
                        ),
                    )

                image_bytes = await image.read()

                if not image_bytes:
                    raise HTTPException(
                        status_code=422,
                        detail="Uploaded image is empty.",
                    )

                if len(image_bytes) > 10 * 1024 * 1024:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Image size must not exceed "
                            "10 MB."
                        ),
                    )

                suffix = Path(
                    image.filename or ""
                ).suffix.lower()

                if suffix not in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                }:
                    suffix = ".img"

                with NamedTemporaryFile(
                    suffix=suffix,
                    delete=False,
                ) as temporary_file:
                    temporary_file.write(image_bytes)
                    temporary_path = temporary_file.name

                state["image_path"] = temporary_path

            result = configured_application.run(state)
            triage = result.get("triage")

            if triage is None:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "The workflow did not produce "
                        "a triage result."
                    ),
                )

            sources = [
                source.model_dump(mode="json")
                for source in result.get(
                    "retrieved_sources",
                    [],
                )
            ]

            return ConsultationResponse(
                consultation_id=state["consultation_id"],
                patient_id=cleaned_patient_id,
                risk_level=triage.risk_level,
                needs_human_review=(
                    triage.needs_human_review
                ),
                response_text=result.get(
                    "response_text",
                    "",
                ),
                retrieved_sources=sources,
            )

        finally:
            if temporary_path is not None:
                Path(temporary_path).unlink(
                    missing_ok=True
                )

    return app