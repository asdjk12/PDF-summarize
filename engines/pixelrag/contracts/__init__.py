"""Stable data contracts shared across the PixelRAG layer."""

from .asset import VisualAsset
from .document import DocumentDescriptor
from .embedding import AssetEmbedding
from .retrieval import RetrievedAsset

__all__ = [
    "AssetEmbedding",
    "DocumentDescriptor",
    "RetrievedAsset",
    "VisualAsset",
]
