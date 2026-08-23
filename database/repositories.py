from io import BytesIO
from typing import Any

from gridfs import GridFSBucket

from database.schemas import Consultation, KnowledgeDocument, Patient


class PatientRepository:
    """Database operations for patient documents."""

    def __init__(self, collection: Any):
        self.collection = collection

    def create(self, patient: Patient) -> Patient:
        self.collection.insert_one(patient.model_dump(mode="json"))
        return patient

    def get_by_id(self, patient_id: str) -> Patient | None:
        document = self.collection.find_one({"patient_id": patient_id})
        return Patient.model_validate(document) if document else None


class ConsultationRepository:
    """Database operations for consultation documents."""

    def __init__(self, collection: Any):
        self.collection = collection

    def create(self, consultation: Consultation) -> Consultation:
        self.collection.insert_one(consultation.model_dump(mode="json"))
        return consultation

    def get_by_id(self, consultation_id: str) -> Consultation | None:
        document = self.collection.find_one({"consultation_id": consultation_id})
        return Consultation.model_validate(document) if document else None

    def list_by_patient(self, patient_id: str, limit: int = 20) -> list[Consultation]:
        documents = self.collection.find({"patient_id": patient_id}).sort("created_at", -1)
        return [Consultation.model_validate(document) for document in documents[:limit]]


class ImageRepository:
    """Store consultation images in MongoDB GridFS."""

    def __init__(self, database: Any, bucket_name: str = "consultation_images"):
        self.bucket = GridFSBucket(database, bucket_name=bucket_name)

    def store(self, image_bytes: bytes, filename: str, content_type: str, patient_id: str) -> str:
        file_id = self.bucket.upload_from_stream(
            filename,
            BytesIO(image_bytes),
            metadata={
                "content_type": content_type,
                "patient_id": patient_id,
                "purpose": "dermtrack_consultation_image",
            },
        )
        return str(file_id)

    def open(self, file_id: str) -> bytes:
        from bson import ObjectId

        output = BytesIO()
        self.bucket.download_to_stream(ObjectId(file_id), output)
        return output.getvalue()


class KnowledgeDocumentRepository:
    """Database operations for RAG knowledge documents."""

    def __init__(self, collection: Any):
        self.collection = collection

    def upsert(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self.collection.replace_one(
            {"source_id": document.source_id},
            document.model_dump(mode="json"),
            upsert=True,
        )
        return document

    def get_by_source_id(self, source_id: str) -> KnowledgeDocument | None:
        document = self.collection.find_one({"source_id": source_id})
        return KnowledgeDocument.model_validate(document) if document else None

    def similarity_search(
        self,
        query_embedding: list[float],
        limit: int = 4,
        index_name: str = "knowledge_vector_index",
    ) -> list[dict[str, Any]]:
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        pipeline = [
            {"$vectorSearch": {
                "index": index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": max(limit * 10, 50),
                "limit": limit,
            }},
            {"$project": {
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
                "score": {"$meta": "vectorSearchScore"},
            }},
        ]

        results = []
        for result in self.collection.aggregate(pipeline):
            score = float(result.pop("score", 0.0))
            results.append({
                "document": KnowledgeDocument.model_validate(result),
                "score": score,
            })
        return results
