from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.tools.repository.schemas import (
    CodeChunk,
    SemanticCandidate,
)


def _qdrant_point_id(chunk_id: str) -> str:
    digest = hashlib.sha1(chunk_id.encode("utf-8")).digest()[:16]
    return str(uuid.UUID(bytes=digest))


class QdrantCodeStore:
    """
    Local persistent Qdrant storage.

    Qdrant runs embedded inside the Python process.

    No:
        Docker
        Qdrant server
        URL
        API key

    Required:
        qdrant_data/ directory
    """

    def __init__(
        self,
        path: str,
        collection_name: str,
        vector_dimension: int,
    ) -> None:

        self.path = Path(path)

        self.path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.collection_name = collection_name

        self.vector_dimension = vector_dimension

        self.client = QdrantClient(
            path=str(self.path)
        )

        self.ensure_collection()

    # ============================================================
    # Collection
    # ============================================================

    def ensure_collection(self) -> None:

        if self.client.collection_exists(
            self.collection_name
        ):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_dimension,
                distance=Distance.COSINE,
            ),
        )

    # ============================================================
    # Information
    # ============================================================

    def collection_exists(self) -> bool:

        return self.client.collection_exists(
            self.collection_name
        )

    def collection_info(self):

        return self.client.get_collection(
            self.collection_name
        )

    # ============================================================
    # Insert / Update
    # ============================================================

    def upsert_chunks(
        self,
        chunks: list[CodeChunk],
        embeddings: list[list[float]],
        batch_size: int = 64,
    ) -> None:

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings "
                "must match."
            )

        for start in range(
            0,
            len(chunks),
            batch_size,
        ):

            chunk_batch = chunks[
                start:start + batch_size
            ]

            embedding_batch = embeddings[
                start:start + batch_size
            ]

            points: list[PointStruct] = []

            for chunk, embedding in zip(
                chunk_batch,
                embedding_batch,
            ):

                points.append(
                    PointStruct(
                        id=_qdrant_point_id(chunk.chunk_id),
                        vector=embedding,
                        payload={
                            "chunk_id": chunk.chunk_id,
                            "repository_id": (
                                chunk.repository_id
                            ),
                            "file_path": (
                                chunk.file_path
                            ),
                            "language": (
                                chunk.language
                            ),
                            "content": (
                                chunk.content
                            ),
                            "start_line": (
                                chunk.start_line
                            ),
                            "end_line": (
                                chunk.end_line
                            ),
                            "chunk_index": (
                                chunk.chunk_index
                            ),
                            "symbol": (
                                chunk.symbol
                            ),
                            "chunk_type": (
                                chunk.chunk_type
                            ),
                            "metadata": (
                                chunk.metadata
                            ),
                        },
                    )
                )

            self.client.upsert(
                collection_name=(
                    self.collection_name
                ),
                points=points,
                wait=True,
            )

    # ============================================================
    # Delete repository
    # ============================================================

    def delete_repository(
        self,
        repository_id: str,
    ) -> None:

        repository_filter = Filter(
            must=[
                FieldCondition(
                    key="repository_id",
                    match=MatchValue(
                        value=repository_id
                    ),
                )
            ]
        )

        self.client.delete(
            collection_name=(
                self.collection_name
            ),
            points_selector=repository_filter,
            wait=True,
        )

    # ============================================================
    # Semantic search
    # ============================================================

    def semantic_search(
        self,
        query_vector: list[float],
        repository_id: str,
        limit: int = 20,
    ) -> list[SemanticCandidate]:

        repository_filter = Filter(
            must=[
                FieldCondition(
                    key="repository_id",
                    match=MatchValue(
                        value=repository_id
                    ),
                )
            ]
        )

        result = self.client.query_points(
            collection_name=(
                self.collection_name
            ),
            query=query_vector,
            query_filter=repository_filter,
            limit=limit,
            with_payload=True,
        )

        candidates: list[
            SemanticCandidate
        ] = []

        for point in result.points:

            payload = point.payload or {}

            candidates.append(
                SemanticCandidate(
                    chunk_id=str(
                        payload.get(
                            "chunk_id",
                            point.id,
                        )
                    ),
                    repository_id=str(
                        payload.get(
                            "repository_id",
                            "",
                        )
                    ),
                    file_path=str(
                        payload.get(
                            "file_path",
                            "",
                        )
                    ),
                    language=str(
                        payload.get(
                            "language",
                            "",
                        )
                    ),
                    content=str(
                        payload.get(
                            "content",
                            "",
                        )
                    ),
                    score=float(
                        point.score
                    ),
                    start_line=int(
                        payload.get(
                            "start_line",
                            0,
                        )
                    ),
                    end_line=int(
                        payload.get(
                            "end_line",
                            0,
                        )
                    ),
                    symbol=payload.get(
                        "symbol"
                    ),
                    chunk_type=str(
                        payload.get(
                            "chunk_type",
                            "code",
                        )
                    ),
                    metadata=payload.get(
                        "metadata",
                        {},
                    ),
                )
            )

        return candidates

    # ============================================================
    # Close
    # ============================================================

    def close(self) -> None:

        self.client.close()
