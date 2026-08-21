from app.config import Settings
from database.mongodb import get_database, ping_database

class FakeDatabase:
    def __init__(self):
        self.commands = []

    def command(self, command_name):
        self.commands.append(command_name)
        return {"ok": 1}

class FakeMongoClient:
    def __init__(self):
        self.requested_database = None
        self.database = FakeDatabase()

    def __getitem__(self, database_name):
        self.requested_database = database_name
        return self.database

def make_test_settings():
    return Settings(
        _env_file=None,
        groq_api_key="test-groq-key",
        google_api_key="test-google-key",
        deepgram_api_key="test-deepgram-key",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_database="test_dermtrack",
    )

def test_get_database_returns_configured_database():
    settings = make_test_settings()
    client = FakeMongoClient()

    database = get_database(settings, client)

    assert database is client.database
    assert client.requested_database == "test_dermtrack"

def test_ping_database_runs_ping_command():
    database = FakeDatabase()

    result = ping_database(database)

    assert result is True
    assert database.commands == ["ping"]