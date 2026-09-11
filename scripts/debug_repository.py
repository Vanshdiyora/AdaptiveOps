from __future__ import annotations

import argparse
from pathlib import Path

from app.services.repository.local import LocalRepositoryProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local repository access for investigation.")
    parser.add_argument("--path", type=str, default=None, help="Repository root to inspect.")
    args = parser.parse_args()

    repo_path = args.path or Path(__file__).resolve().parents[1]
    provider = LocalRepositoryProvider(repo_path)
    print(f"Repository root: {provider.root}")
    print("\nTree:")
    print(provider.get_tree(max_depth=3, max_files=40))
    print("\nFiles:")
    for item in provider.list_files(max_files=20):
        print(f"- {item}")
    print("\nSearch (timeout):")
    for match in provider.search("timeout", max_results=5):
        print(f"{match['file']}:{match['line']} -> {match['match']}")
    print("\nRead sample:")
    sample = provider.list_files(max_files=20)
    if sample:
        read_value = provider.read_file(sample[0], 1, 20)
        print(read_value["file"])
        print(read_value["snippet"])


if __name__ == "__main__":
    main()
