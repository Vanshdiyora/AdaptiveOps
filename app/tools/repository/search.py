from __future__ import annotations

import re

from app.config.settings import settings
from app.tools.repository.embeddings import (
    CodeEmbeddingModel,
)
from app.tools.repository.qdrant_store import (
    QdrantCodeStore,
)
from app.tools.repository.schemas import (
    InvestigationSignal,
    RepositorySearchResult,
    SemanticCandidate,
)


class RepositorySemanticSearch:
    """Semantic repository search."""

    def __init__(self) -> None:
        self.embedding_model = CodeEmbeddingModel(
            model_name=settings.repository_embedding_model,
            max_seq_length=settings.repository_embedding_max_seq_length,
        )
        self.store = QdrantCodeStore(
            path=settings.qdrant_path,
            collection_name=settings.qdrant_collection,
            vector_dimension=self.embedding_model.dimension,
        )

    def search(
        self,
        query: str,
        repository_id: str,
        top_k: int | None = None,
    ) -> list[SemanticCandidate]:
        if not query.strip():
            return []

        query_vector = self.embedding_model.encode_query(query)
        return self.store.semantic_search(
            query_vector=query_vector,
            repository_id=repository_id,
            limit=top_k or settings.repository_semantic_top_k,
        )


class HybridRepositorySearch:
    """Compatibility wrapper used by the investigation engine."""

    def __init__(self, repository, index):
        self.repository = repository
        self.index = index

    @staticmethod
    def _tokenize(value: str) -> list[str]:
        return [
            token.lower()
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_./-]*", value or "")
            if len(token) >= 3
        ]

    async def search(
        self,
        signal: InvestigationSignal,
        *,
        limit: int = 10,
        candidate_limit: int = 50,
    ) -> list[RepositorySearchResult]:
        tokens = []
        for value in [
            signal.exception_type,
            signal.message,
            signal.operation,
            *[frame.function_name or "" for frame in signal.frames],
            *signal.identifiers,
        ]:
            tokens.extend(self._tokenize(value))

        terms = list(dict.fromkeys(tokens))[:8]
        if not terms:
            return []

        seen: set[tuple[str, int, str]] = set()
        results: list[RepositorySearchResult] = []

        for query in terms[:5]:
            try:
                matches = self.repository.search(query, max_results=max(5, candidate_limit), context_lines=2)
            except (OSError, ValueError, RuntimeError):
                continue

            for match in matches:
                file_path = str(match.get("file", ""))
                line_number = int(match.get("line", 1) or 1)
                content = str(match.get("match", ""))
                key = (file_path, line_number, content)
                if not file_path or key in seen:
                    continue
                seen.add(key)
                symbol_name = None
                if "def " in content or "class " in content:
                    match_name = re.search(r"(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", content)
                    if match_name:
                        symbol_name = match_name.group(1)
                results.append(
                    RepositorySearchResult(
                        file_path=file_path,
                        line_number=line_number,
                        score=0.75,
                        symbol_name=symbol_name,
                        content=content,
                        matched_text=content,
                    )
                )

        if not results:
            combined = " ".join(terms)
            try:
                matches = self.repository.search(combined, max_results=max(5, candidate_limit), context_lines=2)
            except (OSError, ValueError, RuntimeError):
                return []
            for match in matches:
                file_path = str(match.get("file", ""))
                line_number = int(match.get("line", 1) or 1)
                content = str(match.get("match", ""))
                if not file_path:
                    continue
                results.append(
                    RepositorySearchResult(
                        file_path=file_path,
                        line_number=line_number,
                        score=0.65,
                        symbol_name=None,
                        content=content,
                        matched_text=content,
                    )
                )

        return results[:limit]


__all__ = [
    "RepositorySemanticSearch",
    "HybridRepositorySearch",
]
