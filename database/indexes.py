from typing import Any

from pymongo import ASCENDING, DESCENDING

def create_indexes(database: Any) -> dict[str, list[str]]:
    """Create indexes required by the application."""

    patients = database["patients"]
    consultations = database["consultations"]
    knowledge_documents = database["knowledge_documents"]
    feedback = database["feedback"]
    agent_runs = database["agent_runs"]

    created_indexes: dict[str, list[str]] = {
        "patients": [],
        "consultations": [],
        "knowledge_documents": [],
        "feedback": [],
        "agent_runs": [],
    }

    patient_index = patients.create_index(
        [("patient_id", ASCENDING)],
        unique=True,
        name="patient_id_unique",
    )
    created_indexes["patients"].append(patient_index)

    consultation_id_index = consultations.create_index(
        [("consultation_id", ASCENDING)],
        unique=True,
        name="consultation_id_unique",
    )
    created_indexes["consultations"].append(consultation_id_index)

    patient_history_index = consultations.create_index(
        [
            ("patient_id", ASCENDING),
            ("created_at", DESCENDING),
        ],
        name="patient_history",
    )
    created_indexes["consultations"].append(patient_history_index)

    risk_level_index = consultations.create_index(
        [("triage.risk_level", ASCENDING)],
        name="risk_level",
    )
    created_indexes["consultations"].append(risk_level_index)

    knowledge_source_index = knowledge_documents.create_index(
        [("source_id", ASCENDING)],
        name="knowledge_source_id",
    )
    created_indexes["knowledge_documents"].append(knowledge_source_index)

    feedback_consultation_index = feedback.create_index(
        [("consultation_id", ASCENDING)],
        name="feedback_consultation_id",
    )
    created_indexes["feedback"].append(feedback_consultation_index)

    agent_run_consultation_index = agent_runs.create_index(
        [("consultation_id", ASCENDING)],
        name="agent_run_consultation_id",
    )
    created_indexes["agent_runs"].append(agent_run_consultation_index)

    return created_indexes