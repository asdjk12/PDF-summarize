from pathlib import Path

from evaluation.retrieval import RetrievalCase
from pdf_knowledge_agent.domain.knowledge import PdfPageLocator
from pdf_knowledge_agent.domain.visual_retrieval import VisualSearchResult
from PixelRAG.evaluation_runner import run_retrieval_evaluation


class QueryResultAdapter:
    """Fake search adapter keyed by the evaluation query text."""

    def __init__(self, pages_by_query):
        self.pages_by_query = pages_by_query
        self.scopes = []

    def search(self, request):
        self.scopes.append(request.source_scope.document_ids)
        return tuple(
            VisualSearchResult(
                document_id="doc-sample",
                page_id=f"doc-sample:page:{page_number}",
                source_locator=PdfPageLocator(page_number),
                score=1.0 / rank,
                representation_ref=f"pixelrag://fake/{page_number}",
            )
            for rank, page_number in enumerate(
                self.pages_by_query[request.query], start=1
            )
        )


def test_runner_uses_real_evaluation_metrics_through_the_search_seam(tmp_path):
    source = tmp_path / "sample.pdf"
    cases = (
        RetrievalCase(
            case_id="formula-001",
            document_id="doc-sample",
            source_file=source,
            query="formula",
            expected_pages=(5,),
            category="formula",
            language="en",
        ),
        RetrievalCase(
            case_id="diagram-001",
            document_id="doc-sample",
            source_file=source,
            query="diagram",
            expected_pages=(8, 9),
            category="diagram",
            language="en",
        ),
    )
    adapter = QueryResultAdapter(
        {"formula": (5, 3), "diagram": (8, 4)}
    )

    report = run_retrieval_evaluation(cases, adapter, top_k=2)

    assert report.metrics.page_hit_rate == 1.0
    assert report.metrics.recall_at_k == 0.75
    assert report.metrics.case_count == 2
    assert report.runs[0].retrieved_pages == (5, 3)
    assert adapter.scopes == [("doc-sample",), ("doc-sample",)]
