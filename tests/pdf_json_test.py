import json
from importlib.util import find_spec
from pathlib import Path

import pytest

from chunking import Chunk
from combine_format import CanonicalDocument, SourceKind, SourceReference
from show_pdf_json_result import build_llm_payload, generate_llm_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_FOLDER = PROJECT_ROOT / "PDF_Folder"
PADDLEOCR_AVAILABLE = find_spec("paddleocr") is not None


def test_build_llm_payload_groups_chunks_by_document():
    document = CanonicalDocument(
        document_id="sample-document",
        source=SourceReference(
            kind=SourceKind.PDF,
            source_name="sample.pdf",
            source_uri="PDF_Folder/sample.pdf",
            mime_type="application/pdf",
            content_sha256="abc123",
            title="Sample",
            languages=("zh", "en"),
            page_count=2,
        ),
        segments=(),
        builder_version="0.2.0",
        merge_strategy="native_first_ocr_supplement",
    )
    chunks = (
        Chunk(
            chunk_id="sample-document:chunk:0",
            ordinal=0,
            document_id="sample-document",
            source_name="sample.pdf",
            text="# 第一节\n\n正文",
            section_path=("第一节",),
            page_numbers=(1, 2),
            block_ids=("block-1", "block-2"),
        ),
    )

    payload = build_llm_payload(
        documents=(document,),
        chunks=chunks,
        input_dir=PDF_FOLDER,
    )

    assert payload["schema_version"] == "1.0"
    assert payload["format"] == "pdf_chunks_for_llm"
    assert payload["document_count"] == 1
    assert payload["chunk_count"] == 1

    output_document = payload["documents"][0]
    assert output_document["document_id"] == "sample-document"
    assert output_document["source"]["source_name"] == "sample.pdf"
    assert output_document["source"]["languages"] == ["zh", "en"]
    assert output_document["canonical"]["builder_version"] == "0.2.0"

    output_chunk = output_document["chunks"][0]
    assert output_chunk["text"] == "# 第一节\n\n正文"
    assert output_chunk["section_path"] == ["第一节"]
    assert output_chunk["page_numbers"] == [1, 2]
    assert output_chunk["block_ids"] == ["block-1", "block-2"]
    assert output_chunk["character_count"] == len(output_chunk["text"])


@pytest.mark.skipif(
    not PDF_FOLDER.is_dir()
    or not any(PDF_FOLDER.glob("*.pdf"))
    or not PADDLEOCR_AVAILABLE,
    reason="集成测试需要 PDF_Folder 中的 PDF 和可选依赖 paddleocr。",
)
def test_pdf_folder_is_converted_to_llm_json(tmp_path):
    output_file = tmp_path / "llm_input.json"
    input_pdf_names = sorted(path.name for path in PDF_FOLDER.glob("*.pdf"))

    payload = generate_llm_json(
        input_dir=PDF_FOLDER,
        output_file=output_file,
    )

    assert output_file.is_file()
    assert json.loads(output_file.read_text(encoding="utf-8")) == payload
    assert payload["document_count"] == len(input_pdf_names)
    assert sorted(
        document["source"]["source_name"]
        for document in payload["documents"]
    ) == input_pdf_names
    assert all(document["chunks"] for document in payload["documents"])
