# DermTrack Agent

DermTrack Agent is a non-diagnostic dermatology-support MVP. It accepts symptom descriptions and optional skin images, performs cautious AI-assisted observations and safety triage, retrieves trusted guidance, generates an educational response, and stores consultations in MongoDB Atlas.

> This project does not diagnose conditions or replace professional medical care.

## Current MVP features

- FastAPI backend
- Text consultations
- JPEG, PNG, and WEBP image uploads
- Gemini Vision non-diagnostic observations
- Conservative safety triage
- Gemini embeddings and MongoDB Atlas Vector Search
- Optional persistent ChromaDB vector store
- Trusted knowledge ingestion and retrieval from Markdown, text, and PDF files
- Optional Tavily web research with trusted-domain allowlisting
- MongoDB consultation persistence
- Patient consultation history
- Minimal browser UI
- Microphone recording with Deepgram transcription
- Deepgram voice playback for generated responses
- Structured patient intake for longitudinal analysis
- MongoDB GridFS storage for uploaded consultation images
- Automated tests

## Requirements

- Windows 10 or later
- Python 3.11
- `uv`
- MongoDB Atlas database
- Configured provider API keys

## Setup

From the repository root:

```powershell
uv sync
Copy-Item .env.example .env
```

Open `.env` and provide local values for the provider keys and MongoDB connection string. Never commit `.env`.

The current Gemini model setting is:

```env
GEMINI_MODEL=gemini-3.6-flash
```

## Run the application

```powershell
uv run uvicorn app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Open the browser UI:

```text
http://127.0.0.1:8000/
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Minimal browser UI |
| GET | `/health` | Service health check |
| POST | `/consultations` | JSON text consultation |
| POST | `/consultations/multimodal` | Multipart text and image consultation |
| POST | `/transcribe` | Deepgram speech-to-text for recorded audio |
| POST | `/speak` | Deepgram text-to-speech response audio |
| GET | `/consultations/{consultation_id}` | Read one stored consultation document |
| GET | `/consultations/{consultation_id}/image` | Read its stored MongoDB GridFS image |
| GET | `/patients/{patient_id}/consultations` | Consultation history |
| GET | `/docs` | Swagger API documentation |

## Text consultation example

```powershell
$body = @{
    patient_id = "demo_patient"
    transcript = "I noticed mild redness on my cheek."
} | ConvertTo-Json -Compress

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/consultations" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body |
    ConvertTo-Json -Depth 10
```

## Image consultation example

```powershell
curl.exe -X POST "http://127.0.0.1:8000/consultations/multimodal" `
    -F "patient_id=demo_image_patient" `
    -F "transcript=I noticed mild redness on my cheek." `
    -F "image=@.\data\demo\synthetic.png;type=image/png"
```

Uploaded PNG, JPEG, and WEBP images are stored in MongoDB GridFS. The consultation document stores the GridFS file ID and content type alongside the transcript, structured patient intake, observations, triage, retrieved sources, and response. Do not store real patient data without appropriate consent and security controls.

## Stored patient intake

The multimodal form accepts symptom onset, duration, progression, affected area, itch and pain severity, triggers, prior treatments, allergies, current medications, medical history, and clinician-provided prescription/follow-up notes. These are stored as `patient_intake` fields for future longitudinal analysis. DermTrack does not generate prescriptions.

## Adding your own RAG sources

Create a UTF-8 `.txt`, `.md`, or `.pdf` file containing trusted educational or clinical-reference content. PDF page numbers are retained in chunk metadata. The ingestion command automatically extracts text, chunks it, creates embeddings, and stores it in the configured vector backend:

```powershell
uv run python -m scripts.ingest_source `
    --source-id aad-eczema-guidance-2026 `
    --title "AAD eczema guidance" `
    --url "https://www.aad.org/public/diseases/eczema" `
    --file .\data\sources\aad-eczema-guidance.pdf `
    --source-type clinical_reference `
    --trust-tier authoritative `
    --tag dermatology `
    --tag eczema
```

The default backend is MongoDB Atlas:

```env
VECTOR_STORE_BACKEND=atlas
```

To use local persistent ChromaDB instead:

```env
VECTOR_STORE_BACKEND=chroma
CHROMA_PERSIST_DIRECTORY=data/chroma
CHROMA_COLLECTION_NAME=dermtrack_knowledge
```

Chroma stores the embeddings and chunks locally. Do not commit `data/chroma`; it contains generated vector data. MongoDB remains the application system of record for consultations and source metadata.

Use authoritative sources such as government health services, recognized dermatology associations, or legally available peer-reviewed references. Do not ingest prescriptions as general guidance. Preserve each source URL, publisher, version, publication date, and license/access information.

## Tavily web research

Tavily is disabled by default. Enable it only after adding your local key to `.env`:

```env
TAVILY_API_KEY=your_local_key
TAVILY_ENABLED=true
TAVILY_MAX_RESULTS=5
TAVILY_ALLOWED_DOMAINS=aad.org,nhs.uk,medlineplus.gov,cdc.gov,who.int,bad.org.uk,nice.org.uk
```

The workflow supports three research modes:

- `local_only`: use ChromaDB or Atlas only.
- `auto`: use Tavily only when local retrieval returns no sources.
- `local_plus_web`: explicitly permit Tavily fallback research.

Web queries are built from de-identified structured observations. DermTrack does not send patient names, IDs, emails, raw transcripts, images, or prescription notes to Tavily. Retrieved web citations are passed into response generation and saved with the consultation.

Tavily is a supplementary research source, not a diagnostic authority. Keep the safety-triage and non-prescriptive response rules active.

## Viewing stored data

MongoDB Atlas shows consultation documents in the `dermtrack.consultations` collection. Uploaded image binaries are in the `dermtrack.consultation_images.files` and `dermtrack.consultation_images.chunks` GridFS collections. RAG chunks are in `dermtrack.knowledge_documents`.

You can also use the API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/patients/demo_image_patient/consultations?limit=10" | ConvertTo-Json -Depth 20
Invoke-RestMethod "http://127.0.0.1:8000/consultations/<consultation_id>" | ConvertTo-Json -Depth 20
```

Open the image endpoint in a browser or download it with:

```powershell
curl.exe -o stored-image.png "http://127.0.0.1:8000/consultations/<consultation_id>/image"
```
## Consultation history example

```powershell
Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/patients/demo_image_patient/consultations?limit=10" `
    -Method Get |
    ConvertTo-Json -Depth 10
```

## Testing

Run the complete test suite:

```powershell
uv run pytest -q
```

The verified MVP suite currently contains 74 passing tests. A Starlette/httpx deprecation warning may appear; it does not indicate a test failure.

## Scope and safety

- Image analysis is observational and non-diagnostic.
- Responses must avoid diagnosis, medication prescriptions, and certainty from images.
- Safety triage routes urgent red flags for human or emergency care; it is not a diagnosis.
- Use synthetic or consented data during development.
- Do not commit `.env`, API keys, passwords, tokens, or connection strings.

## Future production work

- Authentication and authorization
- Secure permanent object storage for media
- Patient consent and account management
- Analytics and feedback workflows
- Observability, rate limiting, and provider timeouts
- Production deployment configuration
- A richer frontend design
