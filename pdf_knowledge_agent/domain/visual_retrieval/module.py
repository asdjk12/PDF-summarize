"""Vendor-independent visual retrieval seam built with Python protocols."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from pdf_knowledge_agent.domain.knowledge import (
    CanonicalPage,
    PdfPageLocator,
    SourceScope,
)


class VisualRetrievalContractError(RuntimeError):
    """Raised when an adapter violates the visual retrieval interface."""


@dataclass(frozen=True, slots=True)
class VisualSearchRequest:
    """A query constrained to an explicit, authorized document scope."""

    query: str
    source_scope: SourceScope
    top_k: int = 5

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("Visual search query must not be blank.")
        if self.top_k < 1:
            raise ValueError("Visual search top_k must be greater than zero.")


@dataclass(frozen=True, slots=True)
class VisualIndexReceipt:
    """Project page identities confirmed as present in a visual index."""

    indexed_page_ids: tuple[str, ...]
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VisualSearchResult:
    """A project-owned page result returned by any visual adapter."""

    document_id: str
    page_id: str
    source_locator: PdfPageLocator
    score: float
    representation_ref: str
    diagnostics: tuple[str, ...] = ()


class VisualRetrievalAdapter(Protocol):
    """The internal adapter slot implemented by PixelRAG or a test fake."""

    def index_pages(
        self,
        pages: Sequence[CanonicalPage],
    ) -> VisualIndexReceipt: ...

    def search(
        self,
        request: VisualSearchRequest,
    ) -> Sequence[VisualSearchResult]: ...


class VisualRetrieval:
    """Validate adapter output before exposing trusted visual page results."""

    def __init__(self, adapter: VisualRetrievalAdapter) -> None:
        self._adapter = adapter

    def index_pages(
        self,
        pages: Sequence[CanonicalPage],
    ) -> VisualIndexReceipt:
        """Index pages only when the adapter preserves every project page ID."""

        expected_page_ids = tuple(page.page_id for page in pages)
        if len(set(expected_page_ids)) != len(expected_page_ids):
            raise VisualRetrievalContractError(
                "Visual retrieval input contains duplicate project page IDs."
            )
        receipt = self._adapter.index_pages(pages)
        if (
            len(receipt.indexed_page_ids) != len(expected_page_ids)
            or set(receipt.indexed_page_ids) != set(expected_page_ids)
        ):
            raise VisualRetrievalContractError(
                "Visual retrieval adapter broke the project page ID mapping."
            )
        return receipt

    def search(
        self,
        request: VisualSearchRequest,
    ) -> tuple[VisualSearchResult, ...]:
        """Return adapter results only when every result stays in scope."""

        results = tuple(self._adapter.search(request))
        if len(results) > request.top_k:
            raise VisualRetrievalContractError(
                "Visual retrieval adapter returned more than top_k results."
            )
        for result in results:
            if not request.source_scope.allows(result.document_id):
                raise VisualRetrievalContractError(
                    "Visual retrieval adapter returned a result outside the "
                    "authorized scope."
                )
        return results
