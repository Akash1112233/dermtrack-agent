from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from database.mongodb import get_database
from database.repositories import (
    ConsultationRepository,
    KnowledgeDocumentRepository,
    PatientRepository,
)

@dataclass(frozen=True)
class Repositories:
    """Application database repositories."""

    patients: PatientRepository
    consultations: ConsultationRepository
    knowledge_documents: KnowledgeDocumentRepository

def build_repositories(
    database: Any | None = None,
    settings: Settings | None = None,
) -> Repositories:
    """Build repositories using a MongoDB database connection."""
    configured_settings = settings or get_settings()
    configured_database = database or get_database(configured_settings)

    return Repositories(
    patients=PatientRepository(
        configured_database["patients"]
    ),
    consultations=ConsultationRepository(
        configured_database["consultations"]
    ),
    knowledge_documents=KnowledgeDocumentRepository(
        configured_database["knowledge_documents"]
    ),
)