from app.config import get_settings
from database.indexes import create_indexes
from database.mongodb import get_database

def main() -> None:
    settings = get_settings()
    database = get_database(settings)
    created_indexes = create_indexes(database)

    for collection_name, indexes in created_indexes.items():
        print(f"{collection_name}: {', '.join(indexes)}")

if __name__ == "__main__":
    main()