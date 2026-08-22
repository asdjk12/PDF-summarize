import pytest

from pdf_knowledge_agent.domain.knowledge import (
    CanonicalPage,
    PdfPageLocator,
    SourceScope,
)
from pdf_knowledge_agent.domain.visual_retrieval import (
    VisualIndexReceipt,
    VisualRetrieval,
    VisualRetrievalContractError,
    VisualSearchRequest,
    VisualSearchResult,
)


class OutOfScopeAdapter:
    """Test adapter that deliberately violates the authorized scope."""

    def search(self, request):
        return (
            VisualSearchResult(
                document_id="doc-private",
                page_id="doc-private:page:1",
                source_locator=PdfPageLocator(page_number=1),
                score=0.98,
                representation_ref="pixelrag://tile/private-1",
            ),
        )


class TooManyResultsAdapter:
    """Test adapter that returns more results than the request permits."""

    def search(self, request):
        return tuple(
            VisualSearchResult(
                document_id="doc-public",
                page_id=f"doc-public:page:{page_number}",
                source_locator=PdfPageLocator(page_number=page_number),
                score=1.0 / page_number,
                representation_ref=f"pixelrag://tile/public-{page_number}",
            )
            for page_number in (1, 2)
        )


class MismatchedIndexAdapter:
    """Test adapter that loses the project's stable page identity."""

    def index_pages(self, pages):
        return VisualIndexReceipt(("vendor-page-1",))

    def search(self, request):
        return ()


class DuplicateIndexAdapter:
    """Test adapter that duplicates one stable page identity."""

    def index_pages(self, pages):
        return VisualIndexReceipt(
            (
                "doc-public:page:1",
                "doc-public:page:1",
                "doc-public:page:2",
            )
        )

    def search(self, request):
        return ()


def test_visual_retrieval_rejects_results_outside_authorized_scope():
    retrieval = VisualRetrieval(OutOfScopeAdapter())
    request = VisualSearchRequest(
        query="architecture diagram",
        source_scope=SourceScope(("doc-public",)),
        top_k=5,
    )

    with pytest.raises(VisualRetrievalContractError, match="authorized scope"):
        retrieval.search(request)


def test_visual_retrieval_enforces_the_requested_top_k_limit():
    retrieval = VisualRetrieval(TooManyResultsAdapter())
    request = VisualSearchRequest(
        query="architecture diagram",
        source_scope=SourceScope(("doc-public",)),
        top_k=1,
    )

    with pytest.raises(VisualRetrievalContractError, match="top_k"):
        retrieval.search(request)


def test_visual_retrieval_preserves_project_page_ids_during_indexing():
    retrieval = VisualRetrieval(MismatchedIndexAdapter())
    page = CanonicalPage(
        page_id="doc-public:page:1",
        document_id="doc-public",
        ordinal=0,
        locator=PdfPageLocator(page_number=1),
        page_image_ref="images/doc-public/page-1.png",
    )

    with pytest.raises(VisualRetrievalContractError, match="page ID mapping"):
        retrieval.index_pages((page,))


def test_visual_retrieval_rejects_duplicate_indexed_page_ids():
    retrieval = VisualRetrieval(DuplicateIndexAdapter())
    pages = tuple(
        CanonicalPage(
            page_id=f"doc-public:page:{page_number}",
            document_id="doc-public",
            ordinal=page_number - 1,
            locator=PdfPageLocator(page_number=page_number),
            page_image_ref=f"images/doc-public/page-{page_number}.png",
        )
        for page_number in (1, 2)
    )

    with pytest.raises(VisualRetrievalContractError, match="page ID mapping"):
        retrieval.index_pages(pages)
