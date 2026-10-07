"""Process-wide embedder. A failed provider stays failed until restart.

Unit tests set EMBEDDING_PROVIDER=none so they never download a model.
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.search.embeddings import (
    EmbeddingProvider,
    LocalEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
)

logger = logging.getLogger(__name__)

_embedder: EmbeddingProvider | bool | None = False


def get_embedder() -> EmbeddingProvider | None:
    global _embedder
    if _embedder is not False:
        return _embedder
    provider = settings.embedding_provider.strip().lower()
    built: EmbeddingProvider | None = None
    if provider == "local":
        built = LocalEmbeddingProvider(settings.embedding_model)
    elif provider == "openai":
        if settings.llm_api_key and settings.llm_base_url:
            built = OpenAICompatibleEmbeddingProvider(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                model_name=settings.embedding_model,
            )
        else:
            logger.warning("embedding provider openai selected but API key or base URL is missing")
    elif provider != "none":
        logger.warning("unknown embedding provider %r; semantic search disabled", provider)
    _embedder = built
    return built


def reset_embedder_for_tests() -> None:
    global _embedder
    _embedder = False
