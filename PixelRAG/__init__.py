"""Isolated Stage 1 integration spike for the external PixelRAG package."""

from .client import (
    PixelRagDocument,
    PixelRagResponseError,
    PixelRagSearchClient,
)
from .evaluation_runner import (
    PixelRagEvaluationReport,
    run_retrieval_evaluation,
)

__all__ = [
    "PixelRagDocument",
    "PixelRagEvaluationReport",
    "PixelRagResponseError",
    "PixelRagSearchClient",
    "run_retrieval_evaluation",
]
