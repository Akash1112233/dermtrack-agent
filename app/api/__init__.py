from uuid import uuid4
from typing import Any
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from pathlib import Path
from tempfile import NamedTemporaryFile
from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator
from agents.state import create_initial_state
from database.schemas import Consultation
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

    @app.get("/", response_class=HTMLResponse)
    def demo_ui() -> str:
        return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DermTrack Agent</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 760px;
      margin: 40px auto; padding: 0 20px; color: #172033; }
    h1 { color: #1e5b83; }
    label { display: block; margin-top: 16px; font-weight: 600; }
    input, textarea { box-sizing: border-box; width: 100%;
      padding: 10px; margin-top: 6px; border: 1px solid #b8c3d1;
      border-radius: 6px; }
    textarea { min-height: 120px; }
    button { margin-top: 20px; padding: 11px 18px; border: 0;
      border-radius: 6px; background: #1e5b83; color: white;
      cursor: pointer; }
    pre { white-space: pre-wrap; background: #f2f5f8; padding: 14px;
      border-radius: 6px; margin-top: 24px; }
    .note { color: #58677a; }
  </style>
</head>
<body>
  <h1>DermTrack Agent</h1>
  <p class="note">Educational support only. This is not a diagnosis.</p>
  <form id="consultation-form">
    <label for="patient_id">Patient ID</label>
    <input id="patient_id" required value="demo_ui_patient">
    <label for="transcript">What did you notice?</label>
    <textarea id="transcript" placeholder="Describe your symptoms..."></textarea>
    <label for="image">Optional skin image</label>
    <input id="image" type="file" accept="image/jpeg,image/png,image/webp">
    <button type="submit">Submit consultation</button>
  </form>
  <pre id="result">Your result will appear here.</pre>
  <script>
    const form = document.getElementById('consultation-form');
    const result = document.getElementById('result');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = new FormData();
      data.append('patient_id', document.getElementById('patient_id').value);
      data.append('transcript', document.getElementById('transcript').value);
      const image = document.getElementById('image').files[0];
      if (image) data.append('image', image);
      result.textContent = 'Processing...';
      try {
        const response = await fetch('/consultations/multimodal', {
          method: 'POST', body: data
        });
        const body = await response.json();
        result.textContent = JSON.stringify(body, null, 2);
      } catch (error) {
        result.textContent = 'Request failed: ' + error;
      }
    });
  </script>
</body>
</html>
        """

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
    @app.get(
        "/patients/{patient_id}/consultations",
        response_model=list[Consultation],
    )
    def get_patient_consultations(
        patient_id: str,
        limit: int = 20,
    ) -> list[Consultation]:
        cleaned_patient_id = patient_id.strip()

        if not cleaned_patient_id:
            raise HTTPException(
                status_code=422,
                detail="patient_id cannot be empty.",
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=422,
                detail="limit must be between 1 and 100.",
            )

        repository = getattr(
            configured_application,
            "consultation_repository",
            None,
        )

        if repository is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Consultation history is not configured."
                ),
            )

        return repository.list_by_patient(
            patient_id=cleaned_patient_id,
            limit=limit,
        )

    return app