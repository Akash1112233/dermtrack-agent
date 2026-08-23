from uuid import uuid4
from typing import Any
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import HTMLResponse, Response
from pathlib import Path
from tempfile import NamedTemporaryFile
from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator
from agents.state import create_initial_state
from database.schemas import Consultation, PatientIntake
from app.application import ConsultationApplication

class ConsultationRequest(BaseModel):
    """Request body for a text consultation."""

    patient_id: str = Field(min_length=1)
    transcript: str = Field(min_length=1)
    patient_intake: PatientIntake = Field(default_factory=PatientIntake)

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

    @app.post("/transcribe")
    async def transcribe_audio(
        audio: UploadFile = File(...),
    ) -> dict[str, str]:
        service = getattr(
            configured_application,
            "deepgram_service",
            None,
        )

        if service is None:
            raise HTTPException(
                status_code=503,
                detail="Deepgram service is not configured.",
            )

        audio_bytes = await audio.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=422,
                detail="Audio file is empty.",
            )

        if len(audio_bytes) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Audio file must not exceed 25 MB.",
            )

        transcript = service.transcribe_bytes(
            audio_bytes=audio_bytes,
            content_type=(
                audio.content_type or "audio/webm"
            ),
        )

        return {"transcript": transcript}

    @app.post("/speak")
    def speak_text(text: str = Form(...)) -> Response:
        service = getattr(
            configured_application,
            "deepgram_service",
            None,
        )

        if service is None:
            raise HTTPException(
                status_code=503,
                detail="Deepgram service is not configured.",
            )

        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail="Text cannot be empty.",
            )

        audio_bytes = service.synthesize(text)

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": (
                    "inline; filename=dermtrack-response.mp3"
                )
            },
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
    :root { --ink: #19324a; --blue: #176b87; --mint: #dff5ef;
      --line: #c8dce0; --card: #ffffff; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, sans-serif; color: var(--ink);
      background: linear-gradient(135deg, #eefaf7, #f4f8ff); }
    .shell { max-width: 900px; margin: 0 auto; padding: 34px 20px 60px; }
    .hero { background: var(--card); border: 1px solid var(--line);
      border-radius: 18px; padding: 28px; box-shadow: 0 12px 35px #17465c12; }
    h1 { margin: 0 0 8px; color: var(--blue); }
    h2 { margin: 0 0 18px; }
    .note { color: #5e7480; }
    .badge { display: inline-block; background: var(--mint); color: #176b60;
      padding: 6px 10px; border-radius: 999px; font-size: 13px; }
    label { display: block; margin-top: 18px; font-weight: 700; }
    input, textarea { box-sizing: border-box; width: 100%; padding: 12px;
      margin-top: 7px; border: 1px solid var(--line); border-radius: 9px;
      background: #fbffff; font: inherit; }
    textarea { min-height: 125px; resize: vertical; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    button { padding: 11px 16px; border: 0; border-radius: 9px;
      background: var(--blue); color: white; cursor: pointer; font-weight: 700; }
    button.secondary { background: #e7f0f2; color: var(--ink); }
    button.recording { background: #bd4057; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    #recording-status { align-self: center; color: #bd4057; font-size: 14px; }
    .result-card { background: #f4f8fa; padding: 18px;
      border: 1px solid var(--line); border-radius: 10px; margin-top: 24px;
      line-height: 1.6; }
    .result-card h3 { margin: 0 0 8px; color: var(--blue); }
    .risk { display: inline-block; padding: 5px 10px; border-radius: 999px;
      background: var(--mint); color: #176b60; font-weight: 700; }
    .risk.urgent { background: #ffe1e6; color: #a1263d; }
    .source-list { padding-left: 20px; }
    details { margin-top: 18px; border: 1px solid var(--line);
      border-radius: 10px; padding: 12px; background: #fbffff; }
    summary { cursor: pointer; font-weight: 700; color: var(--blue); }
    .intake-grid { display: grid; grid-template-columns: repeat(2, 1fr);
      gap: 10px; margin-top: 8px; }
    @media (max-width: 650px) { .intake-grid { grid-template-columns: 1fr; } }

  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="badge">Skin health support</span>
      <h1>DermTrack Agent</h1>
      <p class="note">Educational support only. This is not a diagnosis.</p>
      <form id="consultation-form">
        <label for="patient_id">Patient ID</label>
        <input id="patient_id" required value="demo_ui_patient">
        <label for="transcript">What did you notice?</label>
        <textarea id="transcript" placeholder="Describe itching, redness, pain, bleeding, when it started, and any changes..."></textarea>
        <details>
          <summary>Add details for future analysis</summary>
          <div class="intake-grid">
            <input name="symptom_onset" placeholder="When did it start?">
            <input name="symptom_duration" placeholder="How long has it lasted?">
            <input name="progression" placeholder="Better, worse, or unchanged?">
            <input name="affected_area" placeholder="Affected body area">
            <input name="itch_severity" type="number" min="0" max="10" placeholder="Itch severity (0-10)">
            <input name="pain_severity" type="number" min="0" max="10" placeholder="Pain severity (0-10)">
            <input name="triggers" placeholder="Possible triggers">
            <input name="prior_treatments" placeholder="Previous treatments">
            <input name="allergies" placeholder="Allergies">
            <input name="current_medications" placeholder="Current medications">
            <input name="medical_history" placeholder="Relevant medical history">
            <input name="clinician_prescription_notes" placeholder="Clinician prescription/follow-up notes">
          </div>
        </details>
        <div class="actions">
          <button id="record-button" type="button">🎙️ Start speaking</button>
          <button id="stop-button" class="secondary" type="button" disabled>Stop recording</button>
          <span id="recording-status"></span>
        </div>
        <label for="image">Optional skin image</label>
        <input id="image" type="file" accept="image/jpeg,image/png,image/webp">
        <div class="actions">
          <button type="submit">Submit consultation</button>
        </div>
      </form>
      <div id="result" class="result-card">Your result will appear here.</div>
      <button id="speak-button" class="secondary" type="button" hidden>🔊 Read response aloud</button>
      <audio id="audio-player" controls hidden></audio>
    </section>
  </main>
  <script>
    const form = document.getElementById('consultation-form');
    const result = document.getElementById('result');
    const transcript = document.getElementById('transcript');
    const recordButton = document.getElementById('record-button');
    const stopButton = document.getElementById('stop-button');
    const status = document.getElementById('recording-status');
    const speakButton = document.getElementById('speak-button');
    const audioPlayer = document.getElementById('audio-player');
    let recorder = null;
    let audioChunks = [];
    let latestResponseText = '';
    let progressTimer = null;

    function escapeHtml(value) {
      return String(value || '').replace(/[&<>\'\"]/g, (character) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
      }[character]));
    }

    function formattedText(value) {
      return escapeHtml(value).split(String.fromCharCode(10)).join('<br>');
    }

    function showProgress() {
      const stages = [
        'Uploading your details...',
        'Reviewing the reported symptoms...',
        'Analyzing the image observations...',
        'Checking safety signals...',
        'Searching trusted skin-care guidance...',
        'Preparing your patient-friendly response...'
      ];
      let index = 0;
      result.innerHTML = '<strong>' + stages[0] + '</strong>';
      progressTimer = setInterval(() => {
        index = Math.min(index + 1, stages.length - 1);
        result.innerHTML = '<strong>' + stages[index] + '</strong>';
      }, 1800);
    }

    function renderResponse(body) {
      const risk = escapeHtml(body.risk_level || 'unknown');
      const urgency = body.needs_human_review
        ? '<p><strong>Human review recommended:</strong> Please seek professional evaluation.</p>'
        : '';
      const sources = (body.retrieved_sources || []).map((source) =>
        '<li>' + escapeHtml(source.title || source.source_id) + '</li>'
      ).join('');
      result.innerHTML = '<span class="risk ' + (risk === 'urgent' ? 'urgent' : '') + '">Risk: ' + risk + '</span>' +
        urgency + '<h3>DermTrack guidance</h3><p>' + formattedText(body.response_text) + '</p>' +
        (sources ? '<h3>Trusted sources</h3><ul class="source-list">' + sources + '</ul>' : '');
    }

    recordButton.addEventListener('click', async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({audio: true});
        recorder = new MediaRecorder(stream);
        audioChunks = [];
        recorder.ondataavailable = (event) => audioChunks.push(event.data);
        recorder.onstop = async () => {
          stream.getTracks().forEach((track) => track.stop());
          const blob = new Blob(audioChunks, {type: 'audio/webm'});
          const data = new FormData();
          data.append('audio', blob, 'recording.webm');
          status.textContent = 'Transcribing with Deepgram...';
          try {
            const response = await fetch('/transcribe', {method: 'POST', body: data});
            const raw = await response.text();
            let body;
            try { body = JSON.parse(raw); }
            catch (_) { throw new Error(raw || 'Transcription request failed'); }
            if (!response.ok) throw new Error(body.detail || 'Transcription failed');
            transcript.value = body.transcript;
            status.textContent = 'Transcript added.';
          } catch (error) { status.textContent = error.message; }
        };
        recorder.start();
        recordButton.disabled = true;
        recordButton.classList.add('recording');
        stopButton.disabled = false;
        status.textContent = 'Recording...';
      } catch (error) { status.textContent = 'Microphone permission is required.'; }
    });

    stopButton.addEventListener('click', () => {
      if (recorder && recorder.state !== 'inactive') recorder.stop();
      recordButton.disabled = false;
      recordButton.classList.remove('recording');
      stopButton.disabled = true;
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = new FormData();
      data.append('patient_id', document.getElementById('patient_id').value);
      data.append('transcript', document.getElementById('transcript').value);
      document.querySelectorAll('.intake-grid [name]').forEach((field) => {
        if (field.value !== '') data.append(field.name, field.value);
      });
      const image = document.getElementById('image').files[0];
      if (image) data.append('image', image);
      showProgress();
      try {
        const response = await fetch('/consultations/multimodal', {
          method: 'POST', body: data
        });
        const raw = await response.text();
        let body;
        try { body = JSON.parse(raw); }
        catch (_) { throw new Error(raw || 'Consultation request failed'); }
        if (!response.ok) throw new Error(body.detail || 'Consultation failed');
        latestResponseText = body.response_text || '';
        speakButton.hidden = !latestResponseText;
        renderResponse(body);
      } catch (error) {
        result.innerHTML = '<strong>Request failed:</strong> ' + escapeHtml(error.message || error);
      } finally {
        clearInterval(progressTimer);
      }
    });

    speakButton.addEventListener('click', async () => {
      speakButton.disabled = true;
      try {
        const data = new URLSearchParams({text: latestResponseText});
        const response = await fetch('/speak', {method: 'POST', body: data});
        if (!response.ok) throw new Error('Voice generation failed');
        const audio = await response.blob();
        audioPlayer.src = URL.createObjectURL(audio);
        audioPlayer.hidden = false;
        await audioPlayer.play();
      } catch (error) { result.innerHTML += '<br><br><strong>' + escapeHtml(error.message) + '</strong>'; }
      finally { speakButton.disabled = false; }
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
            patient_intake=request.patient_intake,
        )
        state["transcript"] = request.transcript

        try:
            result = configured_application.run(state)
        except ValueError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

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
        symptom_onset: str = Form(""),
        symptom_duration: str = Form(""),
        progression: str = Form(""),
        affected_area: str = Form(""),
        itch_severity: int | None = Form(default=None),
        pain_severity: int | None = Form(default=None),
        triggers: str = Form(""),
        prior_treatments: str = Form(""),
        allergies: str = Form(""),
        current_medications: str = Form(""),
        medical_history: str = Form(""),
        clinician_prescription_notes: str = Form(""),
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
            state["patient_intake"] = PatientIntake(
                symptom_onset=symptom_onset.strip(),
                symptom_duration=symptom_duration.strip(),
                progression=progression.strip(),
                affected_area=affected_area.strip(),
                itch_severity=itch_severity,
                pain_severity=pain_severity,
                triggers=triggers.strip(),
                prior_treatments=prior_treatments.strip(),
                allergies=allergies.strip(),
                current_medications=current_medications.strip(),
                medical_history=medical_history.strip(),
                clinician_prescription_notes=clinician_prescription_notes.strip(),
            )

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

                image_repository = getattr(
                    configured_application,
                    "image_repository",
                    None,
                )
                if image_repository is not None:
                    state["image_file_id"] = image_repository.store(
                        image_bytes=image_bytes,
                        filename=image.filename or "consultation-image",
                        content_type=image.content_type,
                        patient_id=cleaned_patient_id,
                    )
                    state["image_content_type"] = image.content_type

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

            try:
                result = configured_application.run(state)
            except ValueError as error:
                raise HTTPException(status_code=502, detail=str(error)) from error
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