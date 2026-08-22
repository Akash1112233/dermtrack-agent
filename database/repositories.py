from typing import Any
from database.schemas import Consultation, KnowledgeDocument, Patient
from database.schemas import Consultation, Patient

class PatientRepository:
    """Database operations for patient documents."""

    def __init__(self, collection: Any):
        self.collection = collection

    def create(self, patient: Patient) -> Patient:
        """Insert a patient document."""
        document = patient.model_dump(mode="json")
        self.collection.insert_one(document)
        return patient

    def get_by_id(self, patient_id: str) -> Patient | None:
        """Retrieve a patient by patient ID."""
        document = self.collection.find_one(
            {"patient_id": patient_id}
        )

        if document is None:
            return None

        return Patient.model_validate(document)

class ConsultationRepository:
    """Database operations for consultation documents."""

    def __init__(self, collection: Any):
        self.collection = collection

    def create(self, consultation: Consultation) -> Consultation:
        """Insert a consultation document."""
        document = consultation.model_dump(mode="json")
        self.collection.insert_one(document)
        return consultation

    def get_by_id(self, consultation_id: str) -> Consultation | None:
        """Retrieve a consultation by consultation ID."""
        document = self.collection.find_one(
            {"consultation_id": consultation_id}
        )

        if document is None:
            return None

        return Consultation.model_validate(document)

    def list_by_patient(
        self,
        patient_id: str,
        limit: int = 20,
    ) -> list[Consultation]:
        """Return the newest consultations for a patient."""
        documents = (
            self.collection
            .find({"patient_id": patient_id})
            .sort("created_at", -1)
        )

        return [
            Consultation.model_validate(document)
            for document in documents[:limit]
        ]

class KnowledgeDocumentRepository:
    """Database operations for RAG knowledge documents."""

    def __init__(self, collection: Any):
        self.collection = collection

    def upsert(
        self,
        document: KnowledgeDocument,
    ) -> KnowledgeDocument:
        """Insert or replace a document using its source ID."""
        serialized_document = document.model_dump(mode="json")

        self.collection.replace_one(
            {"source_id": document.source_id},
            serialized_document,
            upsert=True,
        )

        return document

    def get_by_source_id(
        self,
        source_id: str,
    ) -> KnowledgeDocument | None:
        """Retrieve a knowledge document by source ID."""
        document = self.collection.find_one(
            {"source_id": source_id}
        )

        if document is None:
            return None

        return KnowledgeDocument.model_validate(document)

    def similarity_search(
        self,
        query_embedding: list[float],
        limit: int = 4,
        index_name: str = "knowledge_vector_index",
    ) -> list[dict[str, Any]]:
        """Search knowledge chunks using MongoDB Atlas Vector Search."""
        if not query_embedding:
            raise ValueError(
                "query_embedding cannot be empty."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        pipeline = [
            {
                "$vectorSearch": {
                    "index": index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(limit * 10, 50),
                    "limit": limit,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "source_id": 1,
                    "title": 1,
                    "content": 1,
                    "source_type": 1,
                    "url": 1,
                    "tags": 1,
                    "metadata": 1,
                    "embedding": 1,
                    "created_at": 1,
                    "score": {
                        "$meta": "vectorSearchScore"
                    },
                }
            },
        ]

        results = []

        for result in self.collection.aggregate(pipeline):
            score = float(result.pop("score", 0.0))

            results.append(
                {
                    "document": KnowledgeDocument.model_validate(
                        result
                    ),
                    "score": score,
                }
            )

        return results
