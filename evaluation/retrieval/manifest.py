"""JSONL loader for human-verified page-retrieval evaluation cases."""

from __future__ import annotations

import json
from pathlib import Path

from .models import RetrievalCase, RetrievalEvaluationError


_REQUIRED_FIELDS = {
    "case_id",
    "document_id",
    "source_file",
    "query",
    "expected_pages",
    "category",
    "language",
}


def load_retrieval_cases(manifest_path: Path) -> tuple[RetrievalCase, ...]:
    """Load and validate every non-empty JSONL row as a retrieval case."""

    selected_path = Path(manifest_path).resolve()
    if not selected_path.is_file():
        raise RetrievalEvaluationError(
            f"Retrieval manifest does not exist: {selected_path}"
        )

    cases: list[RetrievalCase] = []
    case_ids: set[str] = set()
    for line_number, raw_line in enumerate(
        selected_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise RetrievalEvaluationError(
                f"Invalid JSON on retrieval manifest line {line_number}."
            ) from exc
        if not isinstance(payload, dict):
            raise RetrievalEvaluationError(
                f"Retrieval manifest line {line_number} must be an object."
            )

        missing_fields = _REQUIRED_FIELDS - payload.keys()
        if missing_fields:
            raise RetrievalEvaluationError(
                f"Retrieval manifest line {line_number} is missing fields: "
                f"{sorted(missing_fields)}"
            )

        source_file = (
            selected_path.parent / str(payload["source_file"])
        ).resolve()
        if not source_file.is_file():
            raise RetrievalEvaluationError(
                f"Retrieval source file does not exist: {source_file}"
            )

        case = RetrievalCase(
            case_id=str(payload["case_id"]),
            document_id=str(payload["document_id"]),
            source_file=source_file,
            query=str(payload["query"]),
            expected_pages=tuple(payload["expected_pages"]),
            category=str(payload["category"]),
            language=str(payload["language"]),
        )
        if case.case_id in case_ids:
            raise RetrievalEvaluationError(
                f"Retrieval manifest contains duplicate case_id: "
                f"{case.case_id}"
            )
        case_ids.add(case.case_id)
        cases.append(case)

    if not cases:
        raise RetrievalEvaluationError(
            "Retrieval manifest must contain at least one case."
        )
    return tuple(cases)
