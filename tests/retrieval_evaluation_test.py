import json
from pathlib import Path

import pytest

from evaluation.retrieval import (
    RetrievalCase,
    RetrievalEvaluationError,
    RetrievalRun,
    evaluate_retrieval,
    load_retrieval_cases,
)


def test_load_retrieval_cases_returns_validated_immutable_cases(tmp_path):
    source_file = tmp_path / "sample.pdf"
    source_file.write_bytes(b"%PDF-placeholder")
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "case_id": "table-001",
                "document_id": "doc-sample",
                "source_file": "sample.pdf",
                "query": "表格中的平滑后概率是多少？",
                "expected_pages": [12],
                "category": "table",
                "language": "zh",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cases = load_retrieval_cases(manifest)

    assert len(cases) == 1
    assert cases[0].case_id == "table-001"
    assert cases[0].source_file == source_file.resolve()
    assert cases[0].expected_pages == (12,)


def test_load_retrieval_cases_rejects_duplicate_case_ids(tmp_path):
    source_file = tmp_path / "sample.pdf"
    source_file.write_bytes(b"%PDF-placeholder")
    row = json.dumps(
        {
            "case_id": "table-001",
            "document_id": "doc-sample",
            "source_file": "sample.pdf",
            "query": "Which table contains the smoothed probability?",
            "expected_pages": [12],
            "category": "table",
            "language": "en",
        }
    )
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(f"{row}\n{row}\n", encoding="utf-8")

    with pytest.raises(RetrievalEvaluationError, match="duplicate case_id"):
        load_retrieval_cases(manifest)


def test_evaluate_retrieval_calculates_page_hit_rate_and_recall_at_k(tmp_path):
    cases = (
        RetrievalCase(
            case_id="formula-001",
            document_id="doc-a",
            source_file=tmp_path / "a.pdf",
            query="Which page defines perplexity?",
            expected_pages=(68,),
            category="formula",
            language="en",
        ),
        RetrievalCase(
            case_id="diagram-001",
            document_id="doc-b",
            source_file=tmp_path / "b.pdf",
            query="Where is the parsing comparison diagram?",
            expected_pages=(109, 110),
            category="diagram",
            language="en",
        ),
    )
    runs = (
        RetrievalRun(
            case_id="formula-001",
            retrieved_pages=(20, 68, 50),
            top_k=3,
        ),
        RetrievalRun(
            case_id="diagram-001",
            retrieved_pages=(109, 80),
            top_k=3,
        ),
    )

    metrics = evaluate_retrieval(cases, runs)

    assert metrics.case_count == 2
    assert metrics.page_hit_rate == 1.0
    assert metrics.recall_at_k == 0.75
    assert metrics.top_k == 3


def test_project_retrieval_manifest_covers_verified_visual_categories():
    manifest = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "retrieval"
        / "cases.jsonl"
    )

    cases = load_retrieval_cases(manifest)

    assert len(cases) == 7
    assert {case.language for case in cases} == {"en", "zh"}
    assert {case.category for case in cases} >= {
        "diagram",
        "formula",
        "mixed_layout",
        "table",
    }
