from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from app.config import Settings

def create_mongo_client(settings: Settings) -> MongoClient:
    """Create a MongoDB client using application settings."""
    return MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5_000,
    )

def get_database(
    settings: Settings,
    client: MongoClient | Any | None = None,
) -> Database | Any:
    """Return the configured MongoDB database."""
    mongo_client = client or create_mongo_client(settings)
    return mongo_client[settings.mongodb_database]

def ping_database(database: Database | Any) -> bool:
    """Verify that the MongoDB database responds to a ping command."""
    database.command("ping")
    return True