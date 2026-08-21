from database.repositories import ConsultationRepository, PatientRepository
from database.schemas import (
    Consultation,
    ImageObservation,
    Patient,
    TriageResult,
)

class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        self.documents.append(document)

        class InsertResult:
            inserted_id = "fake-inserted-id"

        return InsertResult()

    def find_one(self, query):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return document

        return None

    def find(self, query):
        matching_documents = [
            document
            for document in self.documents
            if all(document.get(key) == value for key, value in query.items())
        ]

        class FakeCursor:
            def sort(self, field, direction):
                reverse = direction == -1
                return sorted(
                    matching_documents,
                    key=lambda document: document.get(field),
                    reverse=reverse,
                )

        return FakeCursor()

def make_patient():
    return Patient(
        patient_id="patient_001",
        consent_for_storage=True,
    )

def make_consultation():
    return Consultation(
        consultation_id="consultation_001",
        patient_id="patient_001",
        transcript="I have redness on my cheek.",
        observations=[
            ImageObservation(
                feature="localized redness",
                confidence=0.75,
                body_area="left cheek",
            )
        ],
        triage=TriageResult(
            risk_level="low",
            red_flags=[],
            needs_human_review=False,
            explanation="No urgent warning signs were identified.",
        ),
        response_text="This is general informational guidance.",
    )

def test_patient_repository_creates_and_retrieves_patient():
    collection = FakeCollection()
    repository = PatientRepository(collection)
    patient = make_patient()

    repository.create(patient)
    retrieved_patient = repository.get_by_id("patient_001")

    assert retrieved_patient is not None
    assert retrieved_patient.patient_id == "patient_001"
    assert retrieved_patient.consent_for_storage is True

def test_consultation_repository_creates_and_retrieves_consultation():
    collection = FakeCollection()
    repository = ConsultationRepository(collection)
    consultation = make_consultation()

    repository.create(consultation)
    retrieved_consultation = repository.get_by_id("consultation_001")

    assert retrieved_consultation is not None
    assert retrieved_consultation.consultation_id == "consultation_001"
    assert retrieved_consultation.patient_id == "patient_001"
    assert retrieved_consultation.triage.risk_level == "low"

def test_consultation_repository_returns_patient_history():
    collection = FakeCollection()
    repository = ConsultationRepository(collection)

    first_consultation = make_consultation()
    second_consultation = make_consultation().model_copy(
        update={"consultation_id": "consultation_002"}
    )

    repository.create(first_consultation)
    repository.create(second_consultation)

    history = repository.list_by_patient("patient_001")

    assert len(history) == 2
    assert all(item.patient_id == "patient_001" for item in history)