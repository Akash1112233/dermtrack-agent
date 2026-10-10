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
    :root {
      --ink: #18324b; --muted: #587084; --blue: #176b87; --blue-dark: #10566e;
      --teal: #147d78; --mint: #e2f5f1; --line: #d7e4e8; --card: #ffffff;
      --canvas: #f3f8fa; --amber: #9a6500; --amber-bg: #fff4d6;
      --red: #a62e42; --red-bg: #ffe5e9; --green: #16734d; --green-bg: #e0f5e9;
      --shadow: 0 14px 36px rgba(24, 65, 88, .09);
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
      color: var(--ink); background: linear-gradient(145deg, #edf8f7 0%, var(--canvas) 52%, #eef3fb 100%); }
    .shell { max-width: 1100px; margin: 0 auto; padding: 28px 20px 64px; }
    .hero { background: var(--card); border: 1px solid var(--line); border-radius: 22px;
      padding: clamp(22px, 4vw, 42px); box-shadow: var(--shadow); }
    .hero-header { display: flex; justify-content: space-between; gap: 24px; align-items: flex-start;
      padding-bottom: 28px; border-bottom: 1px solid var(--line); }
    .eyebrow, .section-kicker { color: var(--teal); text-transform: uppercase; letter-spacing: .1em;
      font-size: 11px; font-weight: 800; }
    h1 { margin: 6px 0 8px; color: var(--blue-dark); font-size: clamp(30px, 4vw, 44px); letter-spacing: -.03em; }
    h2 { margin: 0; font-size: 21px; }
    h3 { margin: 0; font-size: 16px; color: var(--blue-dark); }
    p { line-height: 1.65; }
    .subtitle, .note { color: var(--muted); max-width: 650px; margin: 0; }
    .privacy-note { max-width: 210px; padding: 12px 14px; border-radius: 12px; background: #f0f7f8;
      color: var(--muted); font-size: 12px; line-height: 1.5; }
    .badge { display: inline-block; background: var(--mint); color: #176b60; padding: 6px 10px;
      border-radius: 999px; font-size: 12px; font-weight: 800; }
    .section { padding-top: 28px; }
    .section-heading { display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px; }
    .section-heading p { margin: 0; color: var(--muted); font-size: 13px; }
    .field-grid, .intake-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .field { min-width: 0; }
    label, .field-label { display: block; margin: 0 0 7px; font-weight: 750; font-size: 14px; }
    input, textarea, select { width: 100%; padding: 12px 13px; border: 1px solid var(--line); border-radius: 10px;
      background: #fcfefe; color: var(--ink); font: inherit; transition: border-color .15s, box-shadow .15s; }
    input:focus, textarea:focus, select:focus, button:focus-visible, summary:focus-visible { outline: 3px solid rgba(23, 107, 135, .22); outline-offset: 2px; border-color: var(--blue); }
    textarea { min-height: 138px; resize: vertical; }
    .help-text { margin: 7px 0 0; color: var(--muted); font-size: 12px; }
    details { margin-top: 18px; border: 1px solid var(--line); border-radius: 12px; padding: 16px; background: #f8fbfc; }
    summary { cursor: pointer; font-weight: 750; color: var(--blue); }
    .intake-grid { margin-top: 18px; }
    .intake-grid input, .intake-grid select { margin: 0; }
    .upload-zone { position: relative; display: grid; place-items: center; min-height: 142px; padding: 20px;
      border: 1.5px dashed #8ab7c0; border-radius: 14px; background: #f6fcfc; text-align: center; cursor: pointer; }
    .upload-zone:hover { background: #eef9f8; border-color: var(--blue); }
    .upload-zone input { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
    .upload-icon { font-size: 25px; }
    .upload-title { display: block; font-weight: 750; margin-top: 6px; }
    .file-meta { color: var(--muted); font-size: 13px; margin-top: 5px; }
    .image-preview { display: none; max-width: 180px; max-height: 130px; margin: 12px auto 0; border-radius: 10px; object-fit: cover; border: 1px solid var(--line); }
    .audio-panel { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 16px; border: 1px solid var(--line); border-radius: 12px; background: #f8fbfc; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; }
    button { padding: 12px 17px; border: 0; border-radius: 10px; background: var(--blue); color: white; cursor: pointer; font-weight: 750; font: inherit; }
    button:hover:not(:disabled) { background: var(--blue-dark); }
    button.secondary { background: #e8f1f3; color: var(--ink); }
    button.secondary:hover:not(:disabled) { background: #dcebed; }
    button.recording { background: #bd4057; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    #recording-status { color: var(--red); font-size: 13px; font-weight: 650; }
    .submit-row { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-top: 24px; }
    .progress-card, .result-card { background: #f8fbfc; padding: 20px; border: 1px solid var(--line); border-radius: 14px; line-height: 1.6; }
    .progress-card { margin-top: 28px; }
    .progress-card[hidden], #speak-button[hidden], #audio-player[hidden] { display: none; }
    .progress-label { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font-size: 13px; }
    .progress-track { height: 7px; margin: 12px 0 15px; border-radius: 99px; background: #dcebed; overflow: hidden; }
    .progress-fill { width: 8%; height: 100%; border-radius: inherit; background: var(--teal); transition: width .35s ease; }
    .progress-steps { display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; margin: 0; padding: 0; list-style: none; }
    .progress-steps li { color: #79909a; font-size: 10px; line-height: 1.3; }
    .progress-steps li.active { color: var(--blue-dark); font-weight: 750; }
    .result-card { margin-top: 18px; background: white; min-height: 150px; }
    .result-placeholder { color: var(--muted); margin: 0; }
    .result-card h3 { margin: 22px 0 8px; }
    .result-card h3:first-child { margin-top: 0; }
    .result-card p { margin: 0 0 10px; }
    .risk { display: inline-flex; align-items: center; padding: 8px 13px; border-radius: 999px; background: var(--green-bg); color: var(--green); font-weight: 800; text-transform: capitalize; }
    .risk.moderate { background: var(--amber-bg); color: var(--amber); }
    .risk.high, .risk.urgent { background: var(--red-bg); color: var(--red); }
    .review-alert, .error-alert { margin: 16px 0; padding: 13px 15px; border-radius: 10px; }
    .review-alert { background: var(--amber-bg); color: #6f4b00; border-left: 4px solid #d79b20; }
    .error-alert { background: var(--red-bg); color: #7d2535; border-left: 4px solid var(--red); }
    .source-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 0; margin: 0; list-style: none; }
    .source-card { padding: 14px; border: 1px solid var(--line); border-radius: 11px; background: #fbfdfd; }
    .source-kind { color: var(--teal); font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; }
    .source-card a { color: var(--blue); font-weight: 700; overflow-wrap: anywhere; }
    .source-meta { display: block; margin-top: 7px; color: var(--muted); font-size: 12px; }
    .result-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
    #audio-player { width: min(100%, 420px); margin-top: 14px; }
    @media (max-width: 700px) { .hero-header, .submit-row { flex-direction: column; } .privacy-note { max-width: none; width: 100%; } .field-grid, .intake-grid, .source-list { grid-template-columns: 1fr; } .progress-steps { grid-template-columns: repeat(3, 1fr); row-gap: 9px; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; } }

  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <header class="hero-header">
        <div>
          <span class="badge">Skin health support</span>
          <h1>DermTrack Agent</h1>
          <p class="subtitle">A structured way to organize skin concerns and explore educational guidance.</p>
        </div>
        <p class="privacy-note">Privacy &amp; safety<br>Use this tool for education only. It is not a diagnosis or a substitute for a clinician.</p>
      </header>
      <form id="consultation-form">
        <section class="section" aria-labelledby="intake-title">
          <div class="section-heading"><div><span class="section-kicker">Step 1</span><h2 id="intake-title">Patient intake</h2></div><p>Share only what you are comfortable providing.</p></div>
          <div class="field-grid">
            <div class="field"><label for="patient_id">Patient ID</label><input id="patient_id" required value="demo_ui_patient" autocomplete="off" aria-describedby="patient-help"><p id="patient-help" class="help-text">A reference used to organize this consultation.</p></div>
            <div class="field"><label for="transcript">What did you notice?</label><textarea id="transcript" placeholder="Describe itching, redness, pain, bleeding, when it started, and any changes..." aria-describedby="symptom-help"></textarea><p id="symptom-help" class="help-text">Include changes over time, symptoms, and anything that makes it better or worse.</p></div>
          </div>
        <details>
          <summary>Add details for a more complete review</summary>
          <div class="intake-grid">
            <select name="symptom_onset" aria-label="When did it start?"><option value="">When did it start?</option><option>Today</option><option>1-7 days ago</option><option>1-4 weeks ago</option><option>1-3 months ago</option><option>More than 3 months ago</option><option>Not sure</option></select>
            <select name="symptom_duration" aria-label="How long has it lasted?"><option value="">How long has it lasted?</option><option>Less than 24 hours</option><option>1-7 days</option><option>1-4 weeks</option><option>1-3 months</option><option>More than 3 months</option></select>
            <select name="progression" aria-label="How is it changing?"><option value="">How is it changing?</option><option>Getting better</option><option>Unchanged</option><option>Getting worse</option><option>Comes and goes</option><option>Not sure</option></select>
            <select name="affected_area" aria-label="Affected body area"><option value="">Affected body area</option><option>Face</option><option>Scalp</option><option>Neck</option><option>Chest or back</option><option>Arms or hands</option><option>Legs or feet</option><option>Multiple areas</option><option>Other</option></select>
            <select name="itch_severity" aria-label="Itch severity from zero to ten"><option value="">Itch severity (0-10)</option><option value="0">0 - None</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5 - Moderate</option><option value="6">6</option><option value="7">7</option><option value="8">8</option><option value="9">9</option><option value="10">10 - Severe</option></select>
            <select name="pain_severity" aria-label="Pain severity from zero to ten"><option value="">Pain severity (0-10)</option><option value="0">0 - None</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5 - Moderate</option><option value="6">6</option><option value="7">7</option><option value="8">8</option><option value="9">9</option><option value="10">10 - Severe</option></select>
            <select name="triggers" aria-label="Possible trigger"><option value="">Possible trigger</option><option>New product or cosmetic</option><option>Food or medicine</option><option>Heat or sweating</option><option>Sun exposure</option><option>Insect bite</option><option>Contact or friction</option><option>Unknown</option></select>
            <input name="prior_treatments" aria-label="Previous treatments" placeholder="Previous treatments">
            <input name="allergies" aria-label="Allergies" placeholder="Allergies">
            <input name="current_medications" aria-label="Current medications" placeholder="Current medications">
            <input name="medical_history" aria-label="Relevant medical history" placeholder="Relevant medical history">
            <input name="clinician_prescription_notes" aria-label="Clinician prescription or follow-up notes" placeholder="Clinician prescription/follow-up notes">
          </div>
        </details>
        </section>
        <section class="section" aria-labelledby="media-title">
          <div class="section-heading"><div><span class="section-kicker">Step 2</span><h2 id="media-title">Add supporting information</h2></div><p>Both options are optional.</p></div>
          <div class="audio-panel"><div class="actions"><button id="record-button" type="button">🎙️ Start speaking</button><button id="stop-button" class="secondary" type="button" disabled>Stop recording</button></div><span id="recording-status" role="status" aria-live="polite">Ready when you are.</span></div>
          <div class="field" style="margin-top: 16px;"><span class="field-label" id="image-label">Optional skin image</span><label class="upload-zone" for="image" aria-describedby="file-meta"><input id="image" type="file" accept="image/jpeg,image/png,image/webp"><span><span class="upload-icon" aria-hidden="true">▧</span><span class="upload-title">Choose an image or drop it here</span><span class="file-meta" id="file-meta">JPEG, PNG, or WebP up to 10 MB</span><img id="image-preview" class="image-preview" alt="Selected skin image preview"></span></label></div>
        </section>
        <div class="submit-row"><p class="note">Your response will include educational guidance and source context.</p><button type="submit">Submit consultation</button></div>
      </form>
      <section id="progress-card" class="progress-card" hidden aria-live="polite" aria-label="Consultation progress"><div class="progress-label"><strong id="progress-stage">Preparing consultation...</strong><span id="progress-count">Step 1 of 6</span></div><div class="progress-track"><div id="progress-fill" class="progress-fill"></div></div><ol id="progress-steps" class="progress-steps"></ol></section>
      <section id="result" class="result-card" aria-live="polite"><p class="result-placeholder">Your consultation summary will appear here after you submit the form.</p></section>
      <div class="result-actions"><button id="speak-button" class="secondary" type="button" hidden>🔊 Read response aloud</button></div>
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
    const progressCard = document.getElementById('progress-card');
    const progressStage = document.getElementById('progress-stage');
    const progressCount = document.getElementById('progress-count');
    const progressFill = document.getElementById('progress-fill');
    const progressSteps = document.getElementById('progress-steps');
    const imageInput = document.getElementById('image');
    const fileMeta = document.getElementById('file-meta');
    const imagePreview = document.getElementById('image-preview');
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
      progressCard.hidden = false;
      progressSteps.innerHTML = stages.map((stage) => '<li>' + escapeHtml(stage) + '</li>').join('');
      updateProgress(index, stages);
      progressTimer = setInterval(() => {
        index = Math.min(index + 1, stages.length - 1);
        updateProgress(index, stages);
      }, 1800);
    }

    function updateProgress(index, stages) {
      progressStage.textContent = stages[index];
      progressCount.textContent = 'Step ' + (index + 1) + ' of ' + stages.length;
      progressFill.style.width = (((index + 1) / stages.length) * 100) + '%';
      Array.from(progressSteps.children).forEach((step, stepIndex) => step.classList.toggle('active', stepIndex === index));
    }

    function safeUrl(value) {
      if (!value) return '';
      try {
        const parsed = new URL(String(value || ''), window.location.origin);
        return ['http:', 'https:'].includes(parsed.protocol) ? parsed.href : '';
      } catch (_) { return ''; }
    }

    function renderResponse(body) {
      const riskValue = String(body.risk_level || 'unknown').toLowerCase();
      const risk = escapeHtml(riskValue);
      const urgency = body.needs_human_review
        ? '<div class="review-alert"><strong>Human review recommended</strong><br>Please seek professional evaluation for next steps.</div>'
        : '';
      const sources = (body.retrieved_sources || []).map((source) => {
        const title = escapeHtml(source.title || source.source_id || 'Source');
        const url = safeUrl(source.url);
        const safeLink = escapeHtml(url);
        const kind = String(source.source_id || '').startsWith('web::')
          ? 'Tavily web research'
          : 'Local RAG source';
        const score = Number.isFinite(Number(source.similarity_score))
          ? 'Relevance ' + Number(source.similarity_score).toFixed(2)
          : 'Reference source';
        const page = source.page_number || source.page || source.metadata?.page;
        const filename = escapeHtml(source.filename || source.file_name || source.source_id || 'Local document');
        const meta = [score, page ? 'Page ' + escapeHtml(page) : '', !url && kind === 'Local RAG source' ? filename : ''].filter(Boolean).join(' · ');
        const link = url
          ? '<a href="' + safeLink + '" target="_blank" rel="noopener noreferrer">' + title + '</a>'
          : title;
        return '<li class="source-card"><span class="source-kind">' + escapeHtml(kind) + '</span><br>' + link + '<span class="source-meta">' + meta + '</span></li>';
      }).join('');
      const riskClass = ['moderate', 'high', 'urgent'].includes(riskValue) ? riskValue : '';
      result.innerHTML = '<span class="risk ' + riskClass + '">Risk level: ' + risk + '</span>' + urgency +
        '<h3>DermTrack guidance</h3><p>' + formattedText(body.response_text || 'No response text was returned.') + '</p>' +
        (sources ? '<h3>Sources used</h3><ul class="source-list">' + sources + '</ul>' : '<h3>Sources used</h3><p>No retrieved sources were available for this consultation.</p>');
    }

    imageInput.addEventListener('change', () => {
      const file = imageInput.files[0];
      if (!file) { fileMeta.textContent = 'JPEG, PNG, or WebP up to 10 MB'; imagePreview.style.display = 'none'; return; }
      fileMeta.textContent = file.name + ' · ' + Math.max(1, Math.round(file.size / 1024)) + ' KB';
      if (file.type.startsWith('image/')) { imagePreview.src = URL.createObjectURL(file); imagePreview.style.display = 'block'; }
    });

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
          } catch (error) { status.textContent = 'Transcription failed. Please try again.'; }
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
        result.innerHTML = '<div class="error-alert"><strong>We could not complete this consultation.</strong><br>Please check your entries and try again.</div>';
      } finally {
        clearInterval(progressTimer);
        progressCard.hidden = true;
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
        audioPlayer.controls = true;
        audioPlayer.load();
        try {
          await audioPlayer.play();
        } catch (_) {
          result.innerHTML += '<br><br><strong>Audio is ready. Press Play on the audio controls.</strong>';
        }
      } catch (error) { result.innerHTML += '<div class="error-alert"><strong>Audio could not be prepared.</strong><br>Please try again or read the response on screen.</div>'; }
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
        "/consultations/{consultation_id}",
        response_model=Consultation,
    )
    def get_consultation(consultation_id: str) -> Consultation:
        consultation = configured_application.consultation_repository.get_by_id(
            consultation_id
        )
        if consultation is None:
            raise HTTPException(status_code=404, detail="Consultation not found")
        return consultation

    @app.get("/consultations/{consultation_id}/image")
    def get_consultation_image(consultation_id: str) -> Response:
        consultation = configured_application.consultation_repository.get_by_id(
            consultation_id
        )
        image_repository = getattr(configured_application, "image_repository", None)
        if consultation is None or not consultation.image_file_id:
            raise HTTPException(status_code=404, detail="Stored image not found")
        if image_repository is None:
            raise HTTPException(status_code=503, detail="Image storage is not configured")
        try:
            image_bytes = image_repository.open(consultation.image_file_id)
        except Exception as error:
            raise HTTPException(status_code=404, detail="Stored image could not be read") from error
        return Response(
            content=image_bytes,
            media_type=consultation.image_content_type or "application/octet-stream",
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
