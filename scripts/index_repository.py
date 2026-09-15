from __future__ import annotations

import argparse

from app.config.settings import settings
from app.tools.repository.indexer import (
    RepositoryIndex,
)


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Build a semantic repository index "
            "using local Qdrant."
        )
    )

    parser.add_argument(
        "repository",
        nargs="?",
        default=None,
        help="Path to the repository.",
    )

    parser.add_argument(
        "--repository-id",
        default=None,
        help=(
            "Optional repository ID. "
            "If omitted, one is generated."
        ),
    )

    args = parser.parse_args()
    repository_path = args.repository or settings.repository_path

    if not repository_path:
        parser.error(
            "repository path is required; pass it as an argument "
            "or set REPOSITORY_PATH in the environment."
        )

    print()
    print(
        f"Indexing repository: "
        f"{repository_path}"
    )

    index = RepositoryIndex()

    result = index.index_repository(
        repository_path=repository_path,
        repository_id=args.repository_id,
    )

    print()
    print("=" * 60)
    print("Repository indexed successfully")
    print("=" * 60)

    for key, value in result.items():
        print(
            f"{key}: {value}"
        )

    print()


if __name__ == "__main__":
    main()