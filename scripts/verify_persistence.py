from uuid import uuid4

from database.container import build_repositories
from database.schemas import Consultation, Patient, TriageResult

def main() -> None:
    repositories = build_repositories()

    patient_id = f"demo_patient_{uuid4().hex[:8]}"
    consultation_id = f"demo_consultation_{uuid4().hex[:8]}"

    patient = Patient(
        patient_id=patient_id,
        consent_for_storage=True,
    )

    consultation = Consultation(
        consultation_id=consultation_id,
        patient_id=patient_id,
        transcript="This is synthetic demo data.",
        triage=TriageResult(
            risk_level="low",
            red_flags=[],
            needs_human_review=False,
            explanation="This is a synthetic low-risk demo record.",
        ),
        response_text=(
            "This is synthetic informational guidance used "
            "to verify database persistence."
        ),
    )

    repositories.patients.create(patient)
    repositories.consultations.create(consultation)

    saved_patient = repositories.patients.get_by_id(patient_id)
    saved_consultation = repositories.consultations.get_by_id(
        consultation_id
    )

    if saved_patient is None:
        raise RuntimeError("Patient was not saved correctly.")

    if saved_consultation is None:
        raise RuntimeError("Consultation was not saved correctly.")

    print("MongoDB persistence verification successful")
    print(f"Patient ID: {saved_patient.patient_id}")
    print(f"Consultation ID: {saved_consultation.consultation_id}")
    print(f"Risk level: {saved_consultation.triage.risk_level}")

if __name__ == "__main__":
    main()