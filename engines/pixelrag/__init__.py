"""Public contracts for the replaceable PixelRAG document engine."""

from .contracts import DocumentDescriptor, RetrievedAsset
from .retrieval import DocumentRetrievalEngine

__all__ = [
    "DocumentDescriptor",
    "DocumentRetrievalEngine",
    "RetrievedAsset",
]
