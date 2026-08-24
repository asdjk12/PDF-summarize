"""Source-document contract received from upstream ingestion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentDescriptor:
    """Describe one upstream-discovered, read-only source document."""

    document_id: str
    source_path: str
    content_hash: str
    mime_type: str
