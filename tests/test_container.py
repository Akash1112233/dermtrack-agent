from database.container import build_repositories

class FakeCollection:
    pass

class FakeDatabase:
    def __init__(self):
        self.collections = {
            "patients": FakeCollection(),
            "consultations": FakeCollection(),
            "knowledge_documents": FakeCollection(),
        }

    def __getitem__(self, collection_name):
        return self.collections[collection_name]

def test_build_repositories_connects_required_collections():
    database = FakeDatabase()

    repositories = build_repositories(database=database)

    assert repositories.patients.collection is database.collections["patients"]
    assert (
        repositories.consultations.collection
        is database.collections["consultations"]
    )
    assert (
        repositories.knowledge_documents.collection
        is database.collections["knowledge_documents"]
    )