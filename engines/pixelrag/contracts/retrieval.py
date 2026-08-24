"""Evidence-candidate contract returned by visual retrieval."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievedAsset:
    """Return one scored asset while retaining source provenance."""

    asset_id: str
    document_id: str
    asset_type: str
    sequence: int
    visual_path: str
    source_location: dict[str, object]
    score: float
    metadata: dict[str, object]
