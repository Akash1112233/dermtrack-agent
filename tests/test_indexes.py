from database.indexes import create_indexes

class FakeCollection:
    def __init__(self):
        self.created_indexes = []

    def create_index(self, keys, **options):
        index_record = {
            "keys": keys,
            "options": options,
        }
        self.created_indexes.append(index_record)
        return options.get("name", "unnamed-index")

class FakeDatabase:
    def __init__(self):
        self.collections = {
            "patients": FakeCollection(),
            "consultations": FakeCollection(),
            "knowledge_documents": FakeCollection(),
            "feedback": FakeCollection(),
            "agent_runs": FakeCollection(),
        }

    def __getitem__(self, collection_name):
        return self.collections[collection_name]

def test_create_indexes_creates_patient_indexes():
    database = FakeDatabase()

    result = create_indexes(database)

    patient_indexes = database.collections["patients"].created_indexes

    assert len(patient_indexes) == 1
    assert patient_indexes[0]["options"]["unique"] is True
    assert "patient_id_unique" in result["patients"]

def test_create_indexes_creates_consultation_indexes():
    database = FakeDatabase()

    result = create_indexes(database)

    consultation_indexes = (
        database.collections["consultations"].created_indexes
    )

    assert len(consultation_indexes) == 3
    assert "consultation_id_unique" in result["consultations"]
    assert "patient_history" in result["consultations"]
    assert "risk_level" in result["consultations"]

def test_create_indexes_returns_all_configured_collections():
    database = FakeDatabase()

    result = create_indexes(database)

    assert "patients" in result
    assert "consultations" in result
    assert "knowledge_documents" in result
    assert "feedback" in result
    assert "agent_runs" in result