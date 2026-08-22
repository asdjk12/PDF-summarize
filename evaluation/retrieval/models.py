"""Immutable retrieval-evaluation models implemented with dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class RetrievalEvaluationError(ValueError):
    """Raised when evaluation inputs violate the manifest contract."""


@dataclass(frozen=True, slots=True)
class RetrievalCase:
    """One query with human-verified relevant PDF page numbers."""

    case_id: str
    document_id: str
    source_file: Path
    query: str
    expected_pages: tuple[int, ...]
    category: str
    language: str

    def __post_init__(self) -> None:
        text_fields = {
            "case_id": self.case_id,
            "document_id": self.document_id,
            "query": self.query,
            "category": self.category,
            "language": self.language,
        }
        for field_name, value in text_fields.items():
            if not value.strip():
                raise RetrievalEvaluationError(
                    f"Retrieval case {field_name} must not be blank."
                )
        if not self.expected_pages:
            raise RetrievalEvaluationError(
                "Retrieval case requires at least one expected page."
            )
        if any(page_number < 1 for page_number in self.expected_pages):
            raise RetrievalEvaluationError(
                "Retrieval case page numbers must be greater than zero."
            )
        if len(set(self.expected_pages)) != len(self.expected_pages):
            raise RetrievalEvaluationError(
                "Retrieval case expected pages must be unique."
            )


@dataclass(frozen=True, slots=True)
class RetrievalRun:
    """The ordered top-k page numbers returned for one evaluation case."""

    case_id: str
    retrieved_pages: tuple[int, ...]
    top_k: int

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise RetrievalEvaluationError(
                "Retrieval run case_id must not be blank."
            )
        if self.top_k < 1:
            raise RetrievalEvaluationError(
                "Retrieval run top_k must be greater than zero."
            )
        if len(self.retrieved_pages) > self.top_k:
            raise RetrievalEvaluationError(
                "Retrieval run contains more than top_k pages."
            )
        if any(page_number < 1 for page_number in self.retrieved_pages):
            raise RetrievalEvaluationError(
                "Retrieved page numbers must be greater than zero."
            )
        if len(set(self.retrieved_pages)) != len(self.retrieved_pages):
            raise RetrievalEvaluationError(
                "Retrieved page numbers must be unique."
            )


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    """Aggregate page-level retrieval measurements for one top-k run."""

    case_count: int
    top_k: int
    page_hit_rate: float
    recall_at_k: float
