import os
from pathlib import Path

import pytest

from evaluation.retrieval import load_retrieval_cases
from pdf_knowledge_agent.domain.knowledge import SourceScope
from pdf_knowledge_agent.domain.visual_retrieval import (
    VisualRetrieval,
    VisualSearchRequest,
)
from PixelRAG.client import PixelRagDocument, PixelRagSearchClient


PIXELRAG_ENDPOINT = os.environ.get("PIXELRAG_TEST_ENDPOINT")


@pytest.mark.skipif(
    not PIXELRAG_ENDPOINT,
    reason="Set PIXELRAG_TEST_ENDPOINT to run the live PixelRAG contract test.",
)
def test_live_pixelrag_search_respects_the_project_contract():
    project_root = Path(__file__).resolve().parents[2]
    cases = load_retrieval_cases(
        project_root / "evaluation" / "retrieval" / "cases.jsonl"
    )
    documents = tuple(
        PixelRagDocument(document_id, source_file)
        for document_id, source_file in dict.fromkeys(
            (case.document_id, case.source_file) for case in cases
        )
    )
    client = PixelRagSearchClient(
        endpoint=PIXELRAG_ENDPOINT,
        documents=documents,
        vendor_working_directory=project_root / "PixelRAG",
    )
    retrieval = VisualRetrieval(client)

    results = retrieval.search(
        VisualSearchRequest(
            query=cases[0].query,
            source_scope=SourceScope((cases[0].document_id,)),
            top_k=5,
        )
    )

    assert len(results) <= 5
    assert all(result.document_id == cases[0].document_id for result in results)
    assert all(result.source_locator.page_number >= 1 for result in results)
