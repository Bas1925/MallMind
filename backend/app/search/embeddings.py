"""Embedding providers.

An embedding is a list of numbers such that texts with similar meaning land
near each other. Cosine similarity is the angle between two of those lists,
independent of their length. It matches concepts ("withdraw money" ~ ATM)
when the model was trained on paraphrases. It does not know the mall; it
only knows the sentences we stored.

pgvector is enough here: 31 locations, 384 dimensions. A dedicated vector
database would add a second system of record for no recall gain.

Calls stay behind this module. Search and reindex never import a vendor SDK.
"""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Protocol

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
DEFAULT_LOCAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingError(Exception):
    pass


class EmbeddingProvider(Protocol):
    model_name: str

    def embed_text(self, text: str) -> list[float]: ...

    def embed_many(self, texts: list[str]) -> list[list[float]]: ...


def _check_dim(vector: list[float], model_name: str) -> list[float]:
    if len(vector) != EMBEDDING_DIM:
        raise EmbeddingError(f"{model_name} returned {len(vector)} dims, expected {EMBEDDING_DIM}")
    return vector


class LocalEmbeddingProvider:
    """fastembed / ONNX. No API key. Model files download on first use."""

    def __init__(self, model_name: str = DEFAULT_LOCAL_MODEL) -> None:
        self.model_name = model_name
        self._model: object | None = None

    def _load(self) -> object:
        if self._model is None:
            try:
                from fastembed import TextEmbedding
            except ImportError as exc:
                raise EmbeddingError(
                    "fastembed is not installed; semantic search is unavailable"
                ) from exc
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = [list(map(float, row)) for row in model.embed(texts)]  # type: ignore[attr-defined]
        return [_check_dim(vector, self.model_name) for vector in vectors]

    def embed_text(self, text: str) -> list[float]:
        rows = self.embed_many([text])
        if not rows:
            raise EmbeddingError("embedder returned no vector")
        return rows[0]


class OpenAICompatibleEmbeddingProvider:
    """POST {base}/embeddings. Used only when an API key is configured."""

    def __init__(self, *, base_url: str, api_key: str, model_name: str) -> None:
        self.model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        import httpx

        if not texts:
            return []
        try:
            response = httpx.post(
                f"{self._base_url}/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self.model_name, "input": texts},
                timeout=20.0,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as exc:
            raise EmbeddingError("embedding provider request failed") from exc
        data = body.get("data")
        if not isinstance(data, list):
            raise EmbeddingError("embedding provider returned an unexpected body")
        ordered = sorted(data, key=lambda item: int(item.get("index", 0)))
        vectors: list[list[float]] = []
        for item in ordered:
            raw = item.get("embedding")
            if not isinstance(raw, list):
                raise EmbeddingError("embedding provider omitted a vector")
            vectors.append(_check_dim([float(value) for value in raw], self.model_name))
        if len(vectors) != len(texts):
            raise EmbeddingError("embedding provider returned the wrong number of vectors")
        return vectors

    def embed_text(self, text: str) -> list[float]:
        return self.embed_many([text])[0]


class HashEmbeddingProvider:
    """Deterministic stand-in for unit tests. Not semantic. Not used in production."""

    model_name = "hash-test"

    def embed_text(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            values = [(digest[index % len(digest)] / 127.5) - 1.0 for index in range(EMBEDDING_DIM)]
            norm = math.sqrt(sum(value * value for value in values)) or 1.0
            vectors.append([value / norm for value in values])
        return vectors


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.7f}" for value in values) + "]"
