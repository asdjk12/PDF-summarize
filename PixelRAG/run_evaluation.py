"""Thin CLI for running the seven-case benchmark against PixelRAG."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from evaluation.retrieval import load_retrieval_cases

from .client import PixelRagDocument, PixelRagSearchClient
from .evaluation_runner import run_retrieval_evaluation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPIKE_ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a local PixelRAG server at the PDF page level."
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("PIXELRAG_ENDPOINT", "http://127.0.0.1:30001"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "evaluation" / "retrieval" / "cases.jsonl",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    cases = load_retrieval_cases(args.manifest)
    documents = tuple(
        PixelRagDocument(document_id, source_file)
        for document_id, source_file in dict.fromkeys(
            (case.document_id, case.source_file) for case in cases
        )
    )
    client = PixelRagSearchClient(
        endpoint=args.endpoint,
        documents=documents,
        vendor_working_directory=SPIKE_ROOT,
    )
    report = run_retrieval_evaluation(cases, client, top_k=args.top_k)
    payload = {
        "metrics": asdict(report.metrics),
        "runs": [asdict(run) for run in report.runs],
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
