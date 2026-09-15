from __future__ import annotations

from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer


class CodeEmbeddingModel:
    """
    Code embedding model wrapper.

    The rest of AdaptiveOps does not need to know
    which embedding library/model is being used.
    """

    def __init__(
        self,
        model_name: str,
        max_seq_length: int = 2048,
    ) -> None:

        self.model_name = model_name

        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
        )

        model_max_length = self.model.max_seq_length
        self.model.max_seq_length = min(
            max_seq_length,
            model_max_length,
        )

    @property
    def dimension(self) -> int:
        dimension = (
            self.model.get_sentence_embedding_dimension()
        )

        if dimension is None:
            raise RuntimeError(
                "Embedding model did not provide "
                "a vector dimension."
            )

        return int(dimension)

    def encode(
        self,
        texts: Sequence[str],
        batch_size: int = 16,
    ) -> list[list[float]]:

        if not texts:
            return []

        embeddings = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        return embeddings.tolist()

    def encode_query(
        self,
        query: str,
    ) -> list[float]:

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        return self.encode(
            [query]
        )[0]
