from __future__ import annotations

from collections import defaultdict
from typing import Callable, Hashable, TypeVar


T = TypeVar("T", bound=Hashable)


def reciprocal_rank_fusion(
    rankings: list[list[T]],
    *,
    k: int = 60,
) -> list[tuple[T, float]]:
    """
    Combine multiple ranked result lists using Reciprocal Rank Fusion.

    RRF score:

        score(d) = sum(1 / (k + rank))

    where rank starts at 1.

    RRF is useful because exact and semantic search produce scores
    that are not directly comparable.
    """
    scores: dict[T, float] = defaultdict(float)

    for ranking in rankings:
        seen: set[T] = set()

        for rank, item in enumerate(ranking, start=1):
            if item in seen:
                continue

            seen.add(item)
            scores[item] += 1.0 / (k + rank)

    return sorted(
        scores.items(),
        key=lambda item: (-item[1], str(item[0])),
    )


def fuse_ranked_results(
    rankings: list[list[T]],
    *,
    key: Callable[[T], Hashable],
    k: int = 60,
) -> list[tuple[T, float]]:
    """
    RRF helper for objects that are not themselves hashable.

    Example:
        key=lambda result: (result.file_path, result.line_number)
    """
    scores: dict[Hashable, float] = defaultdict(float)
    objects: dict[Hashable, T] = {}

    for ranking in rankings:
        seen: set[Hashable] = set()

        for rank, item in enumerate(ranking, start=1):
            item_key = key(item)

            if item_key in seen:
                continue

            seen.add(item_key)
            objects[item_key] = item
            scores[item_key] += 1.0 / (k + rank)

    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], str(item[0])),
    )

    return [(objects[item_key], score) for item_key, score in ranked]