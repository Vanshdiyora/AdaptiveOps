from __future__ import annotations

import argparse

from app.tools.repository.search import (
    RepositorySemanticSearch,
)


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Semantic search over a repository."
        )
    )

    parser.add_argument(
        "repository_id",
        help="Repository ID used during indexing.",
    )

    parser.add_argument(
        "query",
        help="Natural language or code query.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to return.",
    )

    args = parser.parse_args()

    search = RepositorySemanticSearch()

    results = search.search(
        query=args.query,
        repository_id=args.repository_id,
        top_k=args.top_k,
    )

    print()

    if not results:
        print("No results found.")
        return

    print(
        f"Found {len(results)} semantic candidates."
    )

    print()

    for index, result in enumerate(
        results,
        start=1,
    ):

        print("=" * 80)

        print(
            f"{index}. "
            f"{result.file_path}:"
            f"{result.start_line}-"
            f"{result.end_line}"
        )

        print(
            f"score={result.score:.4f}"
        )

        print(
            f"language={result.language}"
        )

        if result.symbol:
            print(
                f"symbol={result.symbol}"
            )

        print("-" * 80)

        print(result.content)

        print()


if __name__ == "__main__":
    main()
