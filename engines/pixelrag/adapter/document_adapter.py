"""Validate and normalize one upstream document with pathlib."""

from __future__ import annotations

from pathlib import Path

from ..contracts import DocumentDescriptor


class UnsupportedDocumentError(ValueError):
    """Raised when a document is outside the PDF-only v1 contract."""


class DocumentAdapter:
    """Prepare one already-discovered PDF for the PixelRAG renderer."""

    PDF_MIME_TYPE = "application/pdf"

    def prepare(self, document: DocumentDescriptor) -> DocumentDescriptor:
        """Validate required fields and return an absolute source path."""

        if not isinstance(document, DocumentDescriptor):
            raise TypeError("document must be a DocumentDescriptor")

        required_fields = (
            "document_id",
            "source_path",
            "content_hash",
            "mime_type",
        )
        for field_name in required_fields:
            value = getattr(document, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        if document.mime_type.strip().casefold() != self.PDF_MIME_TYPE:
            raise UnsupportedDocumentError(
                f"unsupported MIME type: {document.mime_type!r}"
            )

        source_path = Path(document.source_path).expanduser()
        if source_path.suffix.casefold() != ".pdf":
            raise UnsupportedDocumentError(
                f"unsupported document extension: {source_path.suffix or '<none>'}"
            )

        try:
            resolved_path = source_path.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"source PDF does not exist: {source_path}") from exc
        if not resolved_path.is_file():
            raise ValueError(f"source PDF is not a file: {resolved_path}")

        return DocumentDescriptor(
            document_id=document.document_id,
            source_path=str(resolved_path),
            content_hash=document.content_hash,
            mime_type=self.PDF_MIME_TYPE,
        )
