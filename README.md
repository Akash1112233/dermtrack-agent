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
- Trusted knowledge ingestion and retrieval
- MongoDB consultation persistence
- Patient consultation history
- Minimal browser UI
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

Uploaded images are written to a temporary file for processing and removed after the workflow finishes. Permanent media storage is not enabled in this MVP.

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

The verified MVP suite currently contains 67 passing tests. A Starlette/httpx deprecation warning may appear; it does not indicate a test failure.

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
