"""Visual-asset contract produced by document rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisualAsset:
    """Represent one traceable visual retrieval unit."""

    asset_id: str
    document_id: str
    asset_type: str
    sequence: int
    visual_path: str
    source_location: dict[str, object]
