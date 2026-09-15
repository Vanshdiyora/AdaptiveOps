from app.config.settings import settings
from app.tools.repository.qdrant_store import (
    QdrantCodeStore,
)


def main() -> None:

    print("Testing local Qdrant...")
    print()

    print(
        f"Path: {settings.qdrant_path}"
    )

    print(
        f"Collection: "
        f"{settings.qdrant_collection}"
    )

    store = QdrantCodeStore(
        path=settings.qdrant_path,
        collection_name=(
            settings.qdrant_collection
        ),
        vector_dimension=(
            settings.repository_embedding_dimension
        ),
    )

    print()
    print("Qdrant initialized successfully.")
    print()

    print(
        f"Collection exists: "
        f"{store.collection_exists()}"
    )

    info = store.collection_info()

    print()
    print("Collection information:")
    print(info)

    store.close()

    print()
    print("Qdrant test completed successfully.")


if __name__ == "__main__":
    main()
