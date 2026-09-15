from __future__ import annotations

import re

from .schemas import InvestigationSignal, RepositorySearchResult


class RepositoryReranker:
    """
    Lightweight dependency-free reranker.

    Phase 1 intentionally does not require an ML reranker.

    It combines:
      - RRF score
      - exact identifier match
      - exception match
      - operation match
      - message-term overlap
      - symbol match
      - file-path match
    """

    def rerank(
        self,
        signal: InvestigationSignal,
        results: list[RepositorySearchResult],
        *,
        limit: int = 10,
    ) -> list[RepositorySearchResult]:

        scored: list[RepositorySearchResult] = []

        query_terms = self._query_terms(signal)

        for result in results:
            score = result.score

            searchable = " ".join(
                [
                    result.file_path,
                    result.symbol_name or "",
                    result.matched_text,
                ]
            ).lower()

            # Exact symbol/path match.
            if result.symbol_name:
                symbol = result.symbol_name.lower()

                if signal.operation and symbol in signal.operation.lower():
                    score += 0.30

                if any(
                    term == symbol
                    for term in query_terms
                ):
                    score += 0.20

            # Exact text/path match.
            for term in query_terms:
                if term and term in searchable:
                    score += 0.025

            # Exception type.
            if signal.exception_type:
                exception_name = signal.exception_type.lower()

                if exception_name in searchable:
                    score += 0.20

            # Operation.
            if signal.operation:
                operation = signal.operation.lower()

                if operation in searchable:
                    score += 0.20

            # Message overlap.
            if signal.message:
                message_terms = set(
                    self._tokenize(signal.message)
                )

                candidate_terms = set(
                    self._tokenize(searchable)
                )

                if message_terms:
                    overlap = len(
                        message_terms & candidate_terms
                    ) / len(message_terms)

                    score += min(0.20, overlap * 0.20)

            scored.append(
                result.model_copy(
                    update={
                        "score": round(
                            min(1.0, score),
                            4,
                        )
                    }
                )
            )

        scored.sort(
            key=lambda item: (
                -item.score,
                item.file_path,
                item.line_number,
            )
        )

        return scored[:limit]

    @staticmethod
    def _query_terms(
        signal: InvestigationSignal,
    ) -> list[str]:

        values = [
            signal.exception_type or "",
            signal.message or "",
            signal.operation or "",
        ]

        values.extend(
            frame.function_name or ""
            for frame in signal.frames
        )

        values.extend(signal.identifiers)

        terms: list[str] = []

        for value in values:
            terms.extend(
                RepositoryReranker._tokenize(value)
            )

        return list(dict.fromkeys(terms))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        result: list[str] = []

        for token in re.findall(
            r"[A-Za-z][A-Za-z0-9_$.-]*",
            text,
        ):
            token = token.lower()

            if len(token) >= 3:
                result.append(token)

        return result