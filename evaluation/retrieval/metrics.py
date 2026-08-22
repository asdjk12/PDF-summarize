"""Deterministic page-level metrics for retrieval evaluation runs."""

from __future__ import annotations

from collections.abc import Sequence

from .models import (
    RetrievalCase,
    RetrievalEvaluationError,
    RetrievalMetrics,
    RetrievalRun,
)


def evaluate_retrieval(
    cases: Sequence[RetrievalCase],
    retrieved_results: Sequence[RetrievalRun],
) -> RetrievalMetrics:
    """Calculate Page Hit Rate and mean Recall@K for complete case runs."""

    if not cases:
        raise RetrievalEvaluationError(
            "Retrieval evaluation requires at least one case."
        )

    cases_by_id = {case.case_id: case for case in cases}
    runs_by_id = {run.case_id: run for run in retrieved_results}
    if len(cases_by_id) != len(cases):
        raise RetrievalEvaluationError(
            "Retrieval evaluation case IDs must be unique."
        )
    if len(runs_by_id) != len(retrieved_results):
        raise RetrievalEvaluationError(
            "Retrieval evaluation run case IDs must be unique."
        )
    if runs_by_id.keys() != cases_by_id.keys():
        missing = sorted(cases_by_id.keys() - runs_by_id.keys())
        extra = sorted(runs_by_id.keys() - cases_by_id.keys())
        raise RetrievalEvaluationError(
            f"Retrieval runs do not match cases; missing={missing}, extra={extra}."
        )

    top_k_values = {run.top_k for run in retrieved_results}
    if len(top_k_values) != 1:
        raise RetrievalEvaluationError(
            "Retrieval runs must use one consistent top_k value."
        )

    hit_count = 0
    recalls: list[float] = []
    for case_id, case in cases_by_id.items():
        retrieved_pages = set(runs_by_id[case_id].retrieved_pages)
        expected_pages = set(case.expected_pages)
        relevant_hits = retrieved_pages & expected_pages
        if relevant_hits:
            hit_count += 1
        recalls.append(len(relevant_hits) / len(expected_pages))

    case_count = len(cases)
    return RetrievalMetrics(
        case_count=case_count,
        top_k=top_k_values.pop(),
        page_hit_rate=hit_count / case_count,
        recall_at_k=sum(recalls) / case_count,
    )
