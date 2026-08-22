from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

class Patient(BaseModel):
    """Anonymous patient profile."""

    patient_id: str = Field(min_length=1)
    consent_for_storage: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class ImageObservation(BaseModel):
    """A non-diagnostic observation extracted from a skin image."""

    feature: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    body_area: str = "unknown"

class TriageResult(BaseModel):
    """Safety classification for a consultation."""

    risk_level: Literal["low", "moderate", "high", "urgent", "unknown"]
    red_flags: list[str] = Field(default_factory=list)
    needs_human_review: bool = False
    explanation: str = Field(min_length=1)

class RetrievedSource(BaseModel):
    """A source returned by the RAG retrieval system."""

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: HttpUrl
    similarity_score: float = Field(ge=0.0, le=1.0)

class Consultation(BaseModel):
    """Complete consultation document stored in MongoDB."""

    consultation_id: str = Field(min_length=1)
    patient_id: str = Field(min_length=1)
    transcript: str = ""
    observations: list[ImageObservation] = Field(default_factory=list)
    triage: TriageResult
    retrieved_sources: list[RetrievedSource] = Field(default_factory=list)
    response_text: str = Field(min_length=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    

class KnowledgeDocument(BaseModel):
    """Trusted document used by the RAG system."""

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    url: HttpUrl
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )