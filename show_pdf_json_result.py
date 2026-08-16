from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from chunking import Chunk
    from combine_format import CanonicalDocument


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "PDF_Folder"
DEFAULT_OUTPUT_FILE = (
    PROJECT_ROOT / "PDF_Output" / "analysis" / "llm_input.json"
)


def build_llm_payload(
    documents: Sequence[CanonicalDocument],
    chunks: Sequence[Chunk],
    input_dir: Path,
) -> dict[str, Any]:
    """Build the only JSON payload that should be handed to an LLM."""

    document_ids = [document.document_id for document in documents]
    if len(document_ids) != len(set(document_ids)):
        raise ValueError("Canonical documents contain duplicate document_id values.")

    known_document_ids = set(document_ids)
    chunks_by_document: dict[str, list[Chunk]] = defaultdict(list)
    for chunk in chunks:
        if chunk.document_id not in known_document_ids:
            raise ValueError(
                f"Chunk {chunk.chunk_id!r} refers to unknown document "
                f"{chunk.document_id!r}."
            )
        chunks_by_document[chunk.document_id].append(chunk)

    output_documents: list[dict[str, Any]] = []
    for document in documents:
        document_chunks = sorted(
            chunks_by_document[document.document_id],
            key=lambda item: item.ordinal,
        )
        source = document.source
        output_documents.append(
            {
                "document_id": document.document_id,
                "source": {
                    "kind": source.kind.value,
                    "source_name": source.source_name,
                    "source_uri": source.source_uri,
                    "mime_type": source.mime_type,
                    "content_sha256": source.content_sha256,
                    "title": source.title,
                    "languages": list(source.languages),
                    "page_count": source.page_count,
                },
                "canonical": {
                    "schema_version": document.schema_version,
                    "builder_version": document.builder_version,
                    "merge_strategy": document.merge_strategy,
                },
                "chunk_count": len(document_chunks),
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "ordinal": chunk.ordinal,
                        "text": chunk.text,
                        "character_count": chunk.character_count,
                        "section_path": list(chunk.section_path),
                        "page_numbers": list(chunk.page_numbers),
                        "block_ids": list(chunk.block_ids),
                    }
                    for chunk in document_chunks
                ],
            }
        )

    return {
        "schema_version": "1.0",
        "format": "pdf_chunks_for_llm",
        "input_directory": str(input_dir.resolve()),
        "document_count": len(output_documents),
        "chunk_count": sum(
            document["chunk_count"] for document in output_documents
        ),
        "documents": output_documents,
    }


def generate_llm_json(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_file: Path = DEFAULT_OUTPUT_FILE,
) -> dict[str, Any]:
    """Convert PDF_Folder PDFs and persist the final structured LLM payload."""

    selected_input_dir = Path(input_dir).resolve()
    selected_output_file = Path(output_file).resolve()
    _validate_input_directory(selected_input_dir)

    # 中间 raw/baseline/OCR/Canonical 文件仅服务于本次运行。使用隔离目录可避免
    # PDF_Output 中旧文件混入新结果，最终只保留调用方指定的 LLM JSON。
    with TemporaryDirectory(prefix="pdf-json-") as temporary_dir:
        from pdf_read import PipelinePaths, main as run_pdf_pipeline

        documents, chunks = run_pdf_pipeline(
            PipelinePaths(
                input_dir=selected_input_dir,
                output_dir=Path(temporary_dir),
            )
        )

    payload = build_llm_payload(
        documents=documents,
        chunks=chunks,
        input_dir=selected_input_dir,
    )
    selected_output_file.parent.mkdir(parents=True, exist_ok=True)
    selected_output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def _validate_input_directory(input_dir: Path) -> None:
    if not input_dir.is_dir():
        raise FileNotFoundError(
            f"PDF input directory does not exist: {input_dir}"
        )
    if not any(input_dir.glob("*.pdf")):
        raise FileNotFoundError(
            f"No PDF files were found in input directory: {input_dir}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert PDF_Folder PDFs into structured JSON for an LLM.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"PDF directory (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Final JSON file (default: {DEFAULT_OUTPUT_FILE})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = generate_llm_json(
        input_dir=args.input_dir,
        output_file=args.output,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nFinal LLM JSON saved to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
