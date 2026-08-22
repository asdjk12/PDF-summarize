import pytest

from pdf_knowledge_agent.domain.knowledge import (
    CanonicalPage,
    PdfPageLocator,
    SourceScope,
)


def test_source_scope_allows_only_explicit_document_ids():
    scope = SourceScope(("doc-alpha", "doc-beta"))

    assert scope.allows("doc-alpha")
    assert not scope.allows("doc-gamma")

    with pytest.raises(ValueError, match="at least one document"):
        SourceScope(())


def test_canonical_page_rejects_invalid_identity_or_source_location():
    with pytest.raises(ValueError, match="page number"):
        PdfPageLocator(page_number=0)

    with pytest.raises(ValueError, match="page ID"):
        CanonicalPage(
            page_id="",
            document_id="doc-alpha",
            ordinal=0,
            locator=PdfPageLocator(page_number=1),
            page_image_ref="images/doc-alpha/page-1.png",
        )
