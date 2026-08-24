"""Embedding contract that preserves visual-asset identity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AssetEmbedding:
    """Associate one embedding vector with its source asset."""

    asset_id: str
    vector: list[float]
