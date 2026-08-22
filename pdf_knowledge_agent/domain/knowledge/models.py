"""Core knowledge models implemented with immutable Python dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PdfPageLocator:
    """A one-based page location in an original PDF source."""

    page_number: int

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("PDF page number must be greater than zero.")


@dataclass(frozen=True, slots=True)
class CanonicalPage:
    """A stable page identity with an opaque rendered-image reference."""

    page_id: str
    document_id: str
    ordinal: int
    locator: PdfPageLocator
    page_image_ref: str
    optional_text: str | None = None

    def __post_init__(self) -> None:
        if not self.page_id.strip():
            raise ValueError("CanonicalPage page ID must not be blank.")
        if not self.document_id.strip():
            raise ValueError("CanonicalPage document ID must not be blank.")
        if self.ordinal < 0:
            raise ValueError("CanonicalPage ordinal must not be negative.")
        if not self.page_image_ref.strip():
            raise ValueError("CanonicalPage image reference must not be blank.")


@dataclass(frozen=True, slots=True)
class SourceScope:
    """An explicit set of document identities authorized for one operation."""

    document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.document_ids:
            raise ValueError("SourceScope requires at least one document.")
        if any(not document_id.strip() for document_id in self.document_ids):
            raise ValueError("SourceScope document IDs must not be blank.")
        if len(set(self.document_ids)) != len(self.document_ids):
            raise ValueError("SourceScope document IDs must be unique.")

    def allows(self, document_id: str) -> bool:
        """Return whether a document belongs to this authorized scope."""

        return document_id in self.document_ids
