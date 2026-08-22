from pathlib import Path

import pytest

from pdf_knowledge_agent.domain.knowledge import SourceScope
from pdf_knowledge_agent.domain.visual_retrieval import VisualSearchRequest
from PixelRAG.client import (
    PixelRagDocument,
    PixelRagResponseError,
    PixelRagSearchClient,
)


class RecordingTransport:
    """In-memory HTTP transport for exercising the public client interface."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, endpoint, payload, timeout_seconds):
        self.calls.append((endpoint, payload, timeout_seconds))
        return self.response


def test_search_maps_pixelrag_pdf_tiles_to_project_pages(tmp_path):
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"%PDF-placeholder")
    transport = RecordingTransport(
        {
            "results": [
                {
                    "hits": [
                        {
                            "score": 0.91,
                            "vector_id": 7,
                            "article_id": 0,
                            "tile_index": 4,
                            "chunk_index": 0,
                            "url": str(source),
                        }
                    ]
                }
            ]
        }
    )
    client = PixelRagSearchClient(
        endpoint="http://127.0.0.1:30001",
        documents=(PixelRagDocument("doc-sample", source),),
        vendor_working_directory=tmp_path,
        transport=transport,
    )

    results = client.search(
        VisualSearchRequest(
            query="Where is the architecture diagram?",
            source_scope=SourceScope(("doc-sample",)),
            top_k=3,
        )
    )

    assert results[0].document_id == "doc-sample"
    assert results[0].page_id == "doc-sample:page:5"
    assert results[0].source_locator.page_number == 5
    assert results[0].representation_ref == "pixelrag://article/0/tile/4/chunk/0"
    assert transport.calls[0][1] == {
        "queries": [{"text": "Where is the architecture diagram?"}],
        "n_docs": 3,
        "include_images": False,
    }


def test_search_filters_vendor_candidates_to_the_authorized_scope(tmp_path):
    allowed_source = tmp_path / "allowed.pdf"
    other_source = tmp_path / "other.pdf"
    allowed_source.write_bytes(b"%PDF-placeholder")
    other_source.write_bytes(b"%PDF-placeholder")
    transport = RecordingTransport(
        {
            "results": [
                {
                    "hits": [
                        {
                            "score": 0.95,
                            "article_id": 1,
                            "tile_index": 6,
                            "chunk_index": 0,
                            "url": str(other_source),
                        },
                        {
                            "score": 0.90,
                            "article_id": 0,
                            "tile_index": 4,
                            "chunk_index": 0,
                            "url": str(allowed_source),
                        },
                    ]
                }
            ]
        }
    )
    client = PixelRagSearchClient(
        endpoint="http://127.0.0.1:30001",
        documents=(
            PixelRagDocument("doc-allowed", allowed_source),
            PixelRagDocument("doc-other", other_source),
        ),
        vendor_working_directory=tmp_path,
        transport=transport,
    )

    results = client.search(
        VisualSearchRequest(
            query="scoped query",
            source_scope=SourceScope(("doc-allowed",)),
            top_k=2,
        )
    )

    assert tuple(result.document_id for result in results) == ("doc-allowed",)
    assert transport.calls[0][1]["n_docs"] == 4


def test_search_rejects_hits_without_a_project_document_mapping(tmp_path):
    known_source = tmp_path / "known.pdf"
    known_source.write_bytes(b"%PDF-placeholder")
    transport = RecordingTransport(
        {
            "results": [
                {
                    "hits": [
                        {
                            "score": 0.5,
                            "vector_id": 9,
                            "article_id": 1,
                            "tile_index": 0,
                            "chunk_index": 0,
                            "url": str(tmp_path / "unknown.pdf"),
                        }
                    ]
                }
            ]
        }
    )
    client = PixelRagSearchClient(
        endpoint="http://127.0.0.1:30001",
        documents=(PixelRagDocument("doc-known", known_source),),
        vendor_working_directory=tmp_path,
        transport=transport,
    )

    with pytest.raises(PixelRagResponseError, match="document mapping"):
        client.search(
            VisualSearchRequest(
                query="unknown document",
                source_scope=SourceScope(("doc-known",)),
                top_k=1,
            )
        )
