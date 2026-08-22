"""Run the canonical retrieval benchmark through a visual search adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from evaluation.retrieval import (
    RetrievalCase,
    RetrievalMetrics,
    RetrievalRun,
    evaluate_retrieval,
)
from pdf_knowledge_agent.domain.knowledge import SourceScope
from pdf_knowledge_agent.domain.visual_retrieval import (
    VisualRetrieval,
    VisualSearchRequest,
    VisualSearchResult,
)


class VisualSearchAdapter(Protocol):
    """Search-only seam used by the Stage 1 evaluation spike."""

    def search(
        self,
        request: VisualSearchRequest,
    ) -> tuple[VisualSearchResult, ...]: ...


@dataclass(frozen=True, slots=True)
class PixelRagEvaluationReport:
    """Page-level metrics together with the runs that produced them."""

    metrics: RetrievalMetrics
    runs: tuple[RetrievalRun, ...]


def run_retrieval_evaluation(
    cases: tuple[RetrievalCase, ...],
    adapter: VisualSearchAdapter,
    *,
    top_k: int = 5,
) -> PixelRagEvaluationReport:
    """Search every case through the project seam and score page recall."""

    retrieval = VisualRetrieval(adapter)
    runs: list[RetrievalRun] = []
    for case in cases:
        results = retrieval.search(
            VisualSearchRequest(
                query=case.query,
                source_scope=SourceScope((case.document_id,)),
                top_k=top_k,
            )
        )
        retrieved_pages = tuple(
            dict.fromkeys(
                result.source_locator.page_number for result in results
            )
        )
        runs.append(
            RetrievalRun(
                case_id=case.case_id,
                retrieved_pages=retrieved_pages,
                top_k=top_k,
            )
        )

    selected_runs = tuple(runs)
    return PixelRagEvaluationReport(
        metrics=evaluate_retrieval(cases, selected_runs),
        runs=selected_runs,
    )
