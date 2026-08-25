# DermTrack Tavily + Multi-Agent + ChromaDB Implementation Plan

> **For Hermes:** Use the `subagent-driven-development` skill to implement this plan task-by-task.

**Goal:** Extend DermTrack from a single workflow into a safety-controlled multi-agent system that combines Tavily web research, ChromaDB vector retrieval, durable source metadata, structured patient history, and auditable longitudinal analysis.

**Architecture:** Keep the current synchronous `/consultations` and `/consultations/multimodal` endpoints compatible. Introduce a LangGraph supervisor that routes work to specialized agents: intake normalization, image observation, safety triage, local RAG retrieval, Tavily research, response synthesis, persistence, and follow-up analytics. Use ChromaDB as the local/development vector store behind a repository interface; keep MongoDB as the system of record for patient/consultation/source metadata and GridFS images. Tavily receives only de-identified symptom summaries, never raw patient identifiers or images.

**Tech Stack:** Python 3.11, LangGraph, Pydantic, MongoDB/PyMongo/GridFS, ChromaDB, Gemini embeddings, Gemini vision/response services, Tavily API, PyMuPDF, optional OCR, pytest, uv.

---

## 1. Target architecture

### 1.1 Agent graph

```text
request
  -> intake_normalizer
  -> parallel:
       image_observer (only when image exists)
       local_rag_retriever (ChromaDB)
       web_researcher (Tavily; only when allowed and useful)
  -> safety_triage
  -> evidence_quality_gate
  -> response_synthesizer
  -> persistence_agent
  -> followup_analytics_event
  -> response
```

The supervisor should not allow agents to bypass safety triage. A red-flag result must route to conservative escalation language and may suppress nonessential web research.

### 1.2 Agentic properties to add

1. **Tool use:** Tavily search, Chroma retrieval, patient-history retrieval, image observation, and persistence tools.
2. **Routing:** Choose text-only, image, local-RAG, web-research, urgent-escalation, or human-review paths.
3. **Parallel execution:** Run image observation and local retrieval concurrently when safe.
4. **Short-term state:** Typed LangGraph state for the current consultation.
5. **Long-term memory:** MongoDB consultation history and structured patient-intake trends; do not treat free-form model text as reliable memory.
6. **Planning:** A bounded research plan with a maximum number of searches/results and a clear stop condition.
7. **Evidence grounding:** Every retrieved source keeps URL/title/page/chunk metadata; response citations must map to retrieved evidence.
8. **Reflection/checking:** A response validator checks non-diagnostic language, prescription restrictions, citation presence, and urgent-warning coverage.
9. **Human-in-the-loop:** Escalate uncertain, high-risk, contradictory, or low-evidence cases for clinician review.
10. **Retries and fallbacks:** Tavily failure falls back to local RAG; Chroma failure falls back to MongoDB/Atlas retrieval if retained; provider quota errors become structured user-facing status.
11. **Observability:** Persist agent trace IDs, node timings, tool calls, source IDs, confidence/quality flags, and failure reasons without storing secrets.
12. **Idempotency:** A consultation ID and source ID prevent duplicate persistence and duplicate ingestion.

---

## 2. Source strategy

### 2.1 Preferred trusted sources

Start with public, authoritative educational material and maintain a source manifest:

- American Academy of Dermatology public patient information: `aad.org`.
- NHS skin-condition and symptom information: `nhs.uk`.
- MedlinePlus/NIH: `medlineplus.gov`.
- CDC skin-related public-health guidance where relevant: `cdc.gov`.
- WHO guidance where relevant: `who.int`.
- British Association of Dermatologists patient information: `bad.org.uk`.
- DermNet NZ educational pages: `dermnetnz.org`, after checking reuse/licensing requirements.
- NICE guidance: `nice.org.uk`, respecting licensing and redistribution terms.
- PubMed metadata and abstracts for research discovery: `pubmed.ncbi.nlm.nih.gov`; ingest full PDFs only when legally available.

Do not ingest random blogs, forum posts, scraped prescription pages, or unverified social-media content into the trusted collection. Keep source type and trust tier in metadata.

### 2.2 PDFs

Supported document classes:

- Official patient-information PDFs.
- Public clinical guidance PDFs.
- Government health-information PDFs.
- Legally available research PDFs.
- Internal clinician-approved protocols, if the project later has permission to store them.

For each PDF store:

```text
source_id
parent_source_id
title
publisher
author
publication_date
revision/version
source_url
license_or_access_note
page_number
section_heading
chunk_index
content_hash
trust_tier
```

Do not commit source PDFs or patient files to Git. Store local source files under an ignored directory such as `data/sources/` and keep a redacted manifest in the repository.

### 2.3 Patient forms and structured intake

Use the current normalized fields as the primary longitudinal form:

- Symptom onset category.
- Duration category.
- Progression.
- Affected body area.
- Itch severity and pain severity.
- Possible triggers.
- Previous treatments.
- Allergies.
- Current medications.
- Relevant medical/skin history.
- Clinician-provided prescription/follow-up notes.

Use dropdowns for categorical fields and free text only where detail is clinically meaningful. If validated instruments are added later—such as DLQI, POEM, Skindex-16, or UAS7—first confirm licensing/permission and add them as explicitly versioned forms. Do not copy proprietary questionnaires into the product without permission.

---

## 3. ChromaDB design

### 3.1 Storage boundary

Create a `VectorStore` protocol so the workflow does not depend directly on Chroma:

```text
rag/vector_store.py
rag/chroma_store.py
rag/mongo_source_catalog.py
```

Recommended development setup:

```text
Chroma PersistentClient path: data/chroma/
Collection: dermtrack_knowledge
```

Chroma stores:

- Chunk text.
- Embeddings.
- Chroma document ID.
- Source metadata.

MongoDB stores:

- Source catalog.
- Ingestion job status.
- Source URL and license note.
- Content hash/version.
- Chroma IDs and chunk counts.
- Consultation evidence references.

This preserves the project’s MongoDB objective without duplicating the full embedding vector in every MongoDB document. A later production decision can switch the vector implementation to Atlas Vector Search behind the same protocol.

### 3.2 Chunking rules

Implement format-aware chunking:

- PDF: split by headings/pages where possible; preserve page number.
- Markdown: split by headings, then size-based windows.
- Plain text: size-based chunks with overlap.
- Tables: preserve table context and source page.
- Scanned PDFs: OCR first, mark `ocr=true`, and lower evidence confidence if extraction quality is poor.

Initial defaults:

```text
chunk_size: 700-1,000 tokens
chunk_overlap: 100-150 tokens
retrieval_limit: 5-8
minimum_similarity: configured and evaluated, not guessed
```

Use the same embedding model and dimensions for ingestion and retrieval. Record embedding model/version in metadata.

### 3.3 Ingestion commands

Replace the one-off demo-only flow with commands such as:

```powershell
uv run python -m scripts.ingest_source `
  --source-id aad-skin-rashes-v1 `
  --title "AAD skin rash guidance" `
  --url "https://example.org/source" `
  --file .\data\sources\aad-skin-rashes.pdf `
  --source-type clinical_reference `
  --trust-tier authoritative `
  --tag rash `
  --tag safety
```

Add:

```text
scripts/ingest_source.py
scripts/list_sources.py
scripts/delete_source.py
scripts/rebuild_chroma.py
```

Ingestion must be idempotent using `source_id + content_hash + chunk_index`.

---

## 4. Tavily integration design

### 4.1 Tavily agent behavior

Create:

```text
services/tavily_service.py
agents/nodes/web_researcher.py
```

The service should support an injectable fake client for tests and expose:

```text
search(query, domains, max_results, topic, time_range)
```

Research query construction must use normalized, de-identified terms, for example:

```text
"persistent itchy red skin changes" "general safety guidance"
```

Never send patient ID, name, email, image bytes, exact free-text transcript, or prescription details to Tavily.

### 4.2 Search controls

- Allowlist trusted domains by default.
- Limit results and query count per consultation.
- Use Tavily only when local Chroma retrieval is insufficient, stale, or the user asks for current information.
- Cache results by normalized query and date.
- Persist source URL/title/snippet/retrieved-at, but do not treat search snippets as definitive evidence.
- Run source-quality filtering before response synthesis.
- Clearly label web sources separately from curated sources.
- If Tavily quota/API access fails, continue with local RAG and state that current web lookup was unavailable.

### 4.3 Safety boundary

Tavily is for evidence discovery, not diagnosis. It must not be used to search for or produce a prescription. The response agent remains constrained to observations, conservative self-care information, warning signs, and professional evaluation.

---

## 5. Multi-agent state and persistence

Extend the typed state in `agents/state.py` with:

```text
trace_id
execution_mode
normalized_intake
image_observations
local_retrieval_results
web_retrieval_results
research_plan
agent_events
source_quality_flags
response_validation
human_review_reason
```

Persist in MongoDB:

- Consultation document.
- Structured intake.
- GridFS image reference.
- Evidence/source references.
- Agent trace summary.
- Tool failure and fallback metadata.
- Follow-up analytics event.

Do not persist API keys, raw authorization headers, or unnecessary raw Tavily requests containing patient text.

---

## 6. Response and safety policy

The synthesizer must produce:

1. What the patient reported.
2. What the image appears to show, using observational language.
3. Relevant evidence with source links.
4. Safe interim steps.
5. Urgent/emergency warning signs.
6. Questions for a healthcare professional.
7. A clear limitation that this is not a diagnosis.

A validator rejects or rewrites output that:

- Claims a definitive diagnosis.
- Prescribes medication or dosing.
- Uses unsupported certainty from an image.
- Omits urgent escalation when triage requires it.
- Includes uncited factual medical claims when evidence was available.

---

# Phased implementation plan

## Phase 0: Architecture and dependency decisions

### Task 0.1: Freeze interfaces before provider work

**Files:**
- Create: `docs/architecture/multi-agent-rag.md`
- Modify: `README.md`

Document the agent graph, state transitions, source trust tiers, Chroma/Mongo boundary, Tavily privacy boundary, fallback behavior, and non-diagnostic safety policy.

**Verification:** Review the document against the architecture above; no implementation yet.

### Task 0.2: Add configuration placeholders

**Files:**
- Modify: `app/config.py`
- Modify: `.env.example`
- Test: `tests/test_config.py`

Add safe placeholders only for Tavily and Chroma settings. Never add real keys.

**Verification:** `uv run pytest tests/test_config.py -q`.

## Phase 1: ChromaDB foundation

### Task 1.1: Add vector-store protocol

**Files:**
- Create: `rag/vector_store.py`
- Test: `tests/test_vector_store.py`

Define upsert, similarity search, delete-by-source, and health methods with source metadata.

### Task 1.2: Implement Chroma adapter

**Files:**
- Create: `rag/chroma_store.py`
- Modify: `pyproject.toml`
- Test: `tests/test_chroma_store.py`

Use an injectable Chroma client and a temporary test directory. Do not connect to production data in unit tests.

**Verification:** Focused tests, then `uv run pytest -q`.

### Task 1.3: Implement PDF/Markdown extraction

**Files:**
- Create: `rag/document_loader.py`
- Create: `rag/pdf_chunking.py`
- Test: `tests/test_document_loader.py`
- Test: `tests/test_pdf_chunking.py`

Test normal PDFs, empty PDFs, malformed files, page metadata, and OCR-needed detection.

### Task 1.4: Replace demo ingestion with idempotent ingestion

**Files:**
- Modify: `rag/ingestion.py`
- Create/modify: `scripts/ingest_source.py`
- Create: `scripts/list_sources.py`
- Create: `scripts/delete_source.py`
- Test: `tests/test_ingestion.py`

Use content hashes and parent-source metadata. Verify rerunning a source does not duplicate chunks.

## Phase 2: Source catalog and inspection

### Task 2.1: Add MongoDB source catalog

**Files:**
- Modify: `database/schemas.py`
- Modify: `database/repositories.py`
- Modify: `database/container.py`
- Test: `tests/test_source_repository.py`

Store source manifest, status, version, hash, chunk count, Chroma IDs, and license/access notes.

### Task 2.2: Add source inspection endpoints

**Files:**
- Modify: `app/api/__init__.py`
- Test: `tests/test_api.py`

Add list/get/delete or disable endpoints with authentication deferred to the production-hardening phase. Clearly label them as development/admin endpoints until authorization exists.

## Phase 3: Tavily provider and web researcher

### Task 3.1: Add injectable Tavily service

**Files:**
- Create: `services/tavily_service.py`
- Modify: `pyproject.toml`
- Modify: `app/config.py`
- Test: `tests/test_tavily_service.py`

Test successful search, empty results, provider error, timeout, domain allowlist, and redaction.

### Task 3.2: Add web researcher node

**Files:**
- Create: `agents/nodes/web_researcher.py`
- Modify: `agents/state.py`
- Test: `tests/test_web_researcher.py`

Implement bounded search, trusted-domain filtering, deduplication, and fallback behavior.

### Task 3.3: Add explicit Tavily privacy tests

**Files:**
- Create: `tests/test_research_privacy.py`

Assert that patient IDs, names, emails, raw image paths, raw transcripts, and prescription notes never enter Tavily queries.

## Phase 4: Multi-agent LangGraph workflow

### Task 4.1: Split existing workflow into typed nodes

**Files:**
- Modify: `agents/workflow.py`
- Create/modify: `agents/nodes/intake_normalizer.py`
- Create/modify: `agents/nodes/image_observer.py`
- Create/modify: `agents/nodes/local_retriever.py`
- Create/modify: `agents/nodes/safety_triage.py`
- Test: `tests/test_agent_nodes.py`

Keep each node independently injectable and testable.

### Task 4.2: Add supervisor routing

**Files:**
- Create: `agents/supervisor.py`
- Modify: `agents/workflow.py`
- Test: `tests/test_supervisor_routing.py`

Test text-only, image, urgent, no-local-evidence, Tavily-failure, and human-review routes.

### Task 4.3: Add parallel safe retrieval

**Files:**
- Modify: `agents/workflow.py`
- Test: `tests/test_parallel_retrieval.py`

Run image observation and local retrieval concurrently only after intake normalization and before final triage/synthesis. Verify deterministic state merging.

### Task 4.4: Add response validator and reflection pass

**Files:**
- Create: `agents/nodes/response_validator.py`
- Modify: `services/gemini_response.py`
- Test: `tests/test_response_validator.py`

Reject diagnosis claims, prescriptions, unsupported certainty, missing safety warnings, and uncited evidence.

### Task 4.5: Persist agent trace summary

**Files:**
- Modify: `database/schemas.py`
- Modify: `database/repositories.py`
- Modify: `agents/workflow.py`
- Test: `tests/test_agent_trace_persistence.py`

Persist node names, durations, fallback events, source references, and final validation status without secrets.

## Phase 5: API and UI integration

### Task 5.1: Preserve existing endpoint compatibility

**Files:**
- Modify: `app/api/__init__.py`
- Test: `tests/test_api.py`

Keep synchronous endpoints working. Add an optional `research_mode` such as `local_only`, `local_plus_web`, or `auto` with a safe default.

### Task 5.2: Add source-management UI or admin commands

**Files:**
- Modify: `app/api/__init__.py`
- Modify: `README.md`
- Test: `tests/test_api.py`

Prefer CLI first; add UI only after source ingestion and authorization boundaries are stable.

### Task 5.3: Improve response citations and fallback messaging

**Files:**
- Modify: `app/api/__init__.py`
- Test: `tests/test_api.py`

Show curated and web evidence separately and disclose when web research was unavailable.

## Phase 6: Evaluation, analytics, and hardening

### Task 6.1: Build a synthetic evaluation set

**Files:**
- Create: `data/evaluation/cases.jsonl`
- Create: `tests/test_agent_evaluation.py`

Include low-risk, urgent, image-present, ambiguous, no-evidence, provider-failure, and privacy cases. Use synthetic data only.

### Task 6.2: Measure retrieval quality

Track:

- Source recall at k.
- Citation correctness.
- Stale/irrelevant source rate.
- Chunk duplication.
- Tavily fallback frequency.
- Latency and token/provider cost.

### Task 6.3: Production safeguards

Before real patient use, add authentication, role-based source administration, consent, audit logs, encryption/access controls, rate limiting, PII redaction, retention/deletion workflows, and monitoring.

---

## Verification gates

After every phase:

```powershell
uv run pytest -q
python -m py_compile <changed Python files>
git diff --check
git status --short
```

Before enabling Tavily in the default workflow:

1. Verify local-only RAG works.
2. Verify Tavily fake-client tests pass.
3. Verify the privacy redaction tests pass.
4. Run one synthetic live Tavily search using a real key outside normal tests.
5. Confirm retrieved URLs and source labels are shown in the response.

Before calling the system multi-agentic:

1. At least four specialized nodes must execute through LangGraph.
2. Supervisor routing must choose different paths based on inputs.
3. At least one tool call must be observable in the trace.
4. Fallback and human-review routes must be tested.
5. Final response must pass the safety validator before persistence.

## Risks and decisions

- **Tavily cost and quota:** default to local Chroma retrieval; use bounded web fallback.
- **Medical misinformation:** allowlisted sources, source metadata, citations, validator, and human review.
- **Privacy:** send only de-identified summaries to Tavily; never send images or raw patient records.
- **Chroma vs Atlas duplication:** use a repository abstraction; Chroma for development and experimentation, MongoDB for metadata and consultations, Atlas as a later production vector backend if needed.
- **PDF copyright/licensing:** store only sources the project is permitted to use; preserve attribution and license notes.
- **Validated forms:** do not copy proprietary questionnaires without permission; use custom structured intake until licensing is confirmed.
- **Complexity:** implement one vertical slice at a time; do not add autonomous loops or unrestricted agents. Every agent has bounded tools, a timeout, and a stop condition.

## Recommended first implementation slice

Start with this narrow, high-value slice:

1. Chroma vector-store adapter.
2. PDF/Markdown ingestion with page/source metadata.
3. One `local_rag_retriever` node.
4. One injectable Tavily service with allowlisted domains.
5. One `web_researcher` fallback node.
6. Supervisor route: local-only versus local-plus-web.
7. Source citations in the existing response.
8. Tests for fake providers, privacy redaction, and fallback.

Do not begin with ten autonomous agents. First prove that local evidence, bounded web research, citations, and safety validation work together.
