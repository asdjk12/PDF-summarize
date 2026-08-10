import hashlib
import json
from pathlib import Path

import pytest

from combine_format import (
    BlockType,
    CanonicalDocument,
    CanonicalSegment,
    ContentSource,
    LocatorKind,
    OcrStatus,
    SourceKind,
    SourceReference,
    build_canonical_document,
    extract_native_blocks,
    map_ocr_diagnostics
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DOCUMENT_NAME = "Week 2 - Language Modelling-CL-2026"
DOCUMENT_ID = "week2-language-modelling"

RAW_PATH = (
    PROJECT_ROOT
    / "PDF_Output"
    / "raw"
    / f"{DOCUMENT_NAME}.json"
)

PDF_PATH = (
    PROJECT_ROOT
    / "PDF_Folder"
    / f"{DOCUMENT_NAME}.pdf"
)

BASELINE_PATH = (
    PROJECT_ROOT
    / "PDF_Output"
    / "analysis"
    / "baseline_analysis.json"
)

OCR_PATH = (
    PROJECT_ROOT
    / "PDF_Output"
    / "analysis"
    / "ocr_results.json"
)


@pytest.fixture(scope="module")
def week2_inputs():
    raw_document = json.loads(
        RAW_PATH.read_text(encoding="utf-8")
    )

    baseline_report = json.loads(
        BASELINE_PATH.read_text(encoding="utf-8")
    )

    ocr_report = json.loads(
        OCR_PATH.read_text(encoding="utf-8")
    )

    baseline_document = baseline_report["documents"][DOCUMENT_NAME]
    ocr_document = ocr_report["document"][DOCUMENT_NAME]

    source = SourceReference(
        kind=SourceKind.PDF,
        source_name=PDF_PATH.name,
        source_uri=str(PDF_PATH),
        mime_type="application/pdf",
        content_sha256=hashlib.sha256(
            PDF_PATH.read_bytes()
        ).hexdigest(),
        title=raw_document.get("title"),
        languages=("en",),
        page_count=int(raw_document["number of pages"]),
    )

    return {
        "raw_document": raw_document,
        "baseline_document": baseline_document,
        "ocr_document": ocr_document,
        "source": source,
    }


def test_step7_extract_native_blocks(week2_inputs):
    """Step 7: OpenDataLoader 节点能够转换为 native ContentBlock。"""

    blocks_by_page = extract_native_blocks(
        week2_inputs["raw_document"],
        document_id=DOCUMENT_ID,
    )

    # Week 2 应当包含完整的 1～74 页。
    assert set(blocks_by_page) == set(range(1, 75))

    all_blocks = [
        block
        for blocks in blocks_by_page.values()
        for block in blocks
    ]

    # 当前 OpenDataLoader 输出快照的预期数量。
    assert len(all_blocks) == 437

    extracted_types = {
        block.type
        for block in all_blocks
    }

    assert BlockType.HEADING in extracted_types
    assert BlockType.PARAGRAPH in extracted_types
    assert BlockType.LIST_ITEM in extracted_types
    assert BlockType.CAPTION in extracted_types
    assert BlockType.TABLE in extracted_types
    assert BlockType.FIGURE in extracted_types

    for page_number, blocks in blocks_by_page.items():
        for expected_ordinal, block in enumerate(blocks):
            assert block.ordinal == expected_ordinal
            assert block.source is ContentSource.NATIVE
            assert block.block_id.startswith(
                f"{DOCUMENT_ID}:page:{page_number}:native:"
            )


def test_step6_and_step7_build_canonical_document(week2_inputs):
    """
    Step 6 + Step 7 集成测试：

    build_canonical_document()
    必须返回结构正确的 CanonicalDocument，
    并且 native blocks 必须进入每页 CanonicalSegment。
    """

    raw_document = week2_inputs["raw_document"]
    baseline_document = week2_inputs["baseline_document"]
    ocr_document = week2_inputs["ocr_document"]
    source = week2_inputs["source"]

    canonical_document = build_canonical_document(
        raw_document=raw_document,
        baseline_document=baseline_document,
        ocr_document=ocr_document,
        document_id=DOCUMENT_ID,
        source=source,
    )

    # ---------------------------------------------------------
    # Step 6：CanonicalDocument 基础结构
    # ---------------------------------------------------------

    assert isinstance(
        canonical_document,
        CanonicalDocument,
    )

    assert canonical_document.document_id == DOCUMENT_ID
    assert canonical_document.source == source
    assert canonical_document.schema_version == "1.0"
    assert canonical_document.builder_version == "0.1.0"
    assert (
        canonical_document.merge_strategy
        == "native_first_ocr_supplement"
    )

    assert len(canonical_document.segments) == 74

    # ---------------------------------------------------------
    # Step 7：取得独立提取结果，用于检查 Builder 是否正确接入
    # ---------------------------------------------------------

    expected_blocks_by_page = extract_native_blocks(
        raw_document,
        document_id=DOCUMENT_ID,
    )

    requested_pages = set(
        baseline_document["needs_ocr_pages"]
    )

    ocr_pages = ocr_document["pages"]

    for page_number, segment in enumerate(
        canonical_document.segments,
        start=1,
    ):
        assert isinstance(segment, CanonicalSegment)

        # PDF 页码从 1 开始；ordinal 从 0 开始。
        assert segment.ordinal == page_number - 1
        assert segment.locator.page_number == page_number
        assert segment.locator.kind is LocatorKind.PDF_PAGE

        assert segment.segment_id == (
            f"{DOCUMENT_ID}:page:{page_number}"
        )

        # Step 6/7 尚未合成最终 content。
        assert segment.content == ""

        # Step 7 的关键集成检查：
        # Builder 中的 blocks 必须等于 native 提取结果。
        assert segment.blocks == expected_blocks_by_page.get(
            page_number,
            (),
        )

        if page_number not in requested_pages:
            assert not segment.diagnostics.ocr_requested
            assert (
                segment.diagnostics.ocr_status
                is OcrStatus.NOT_REQUESTED
            )

        elif str(page_number) in ocr_pages:
            assert segment.diagnostics.ocr_requested
            assert (
                segment.diagnostics.ocr_status
                is OcrStatus.SUCCEEDED
            )

        else:
            assert segment.diagnostics.ocr_requested
            assert (
                segment.diagnostics.ocr_status
                is OcrStatus.MISSING
            )

    # ---------------------------------------------------------
    # Step 6 + Step 7 最终整体检查
    # ---------------------------------------------------------

    all_canonical_blocks = [
        block
        for segment in canonical_document.segments
        for block in segment.blocks
    ]

    # 这一项能检测 blocks=() 之类的接线错误。
    assert len(all_canonical_blocks) == 437

    assert all(
        block.source is ContentSource.NATIVE
        for block in all_canonical_blocks
    )

    assert sum(
        segment.diagnostics.ocr_requested
        for segment in canonical_document.segments
    ) == 31

    assert sum(
        segment.diagnostics.ocr_status is OcrStatus.SUCCEEDED
        for segment in canonical_document.segments
    ) == 31


def test_step6_rejects_page_count_mismatch(week2_inputs):
    """Step 6: raw 和 baseline 页数不一致时必须拒绝构造。"""

    invalid_baseline = dict(
        week2_inputs["baseline_document"]
    )

    invalid_baseline["page_count"] = 73

    with pytest.raises(
        ValueError,
        match="page counts do not match",
    ):
        build_canonical_document(
            raw_document=week2_inputs["raw_document"],
            baseline_document=invalid_baseline,
            ocr_document=week2_inputs["ocr_document"],
            document_id=DOCUMENT_ID,
            source=week2_inputs["source"],
        )

def test_step8_map_all_ocr_statuses():
    """Step 8：一次性测试所有 baseline/OCR 状态映射。"""

    test_cases = [
        {
            "name": "not requested",
            "baseline_page": {
                "needs_ocr": False,
            },
            "ocr_page": None,
            "expected_requested": False,
            "expected_status": OcrStatus.NOT_REQUESTED,
        },
        {
            "name": "missing OCR page",
            "baseline_page": {
                "needs_ocr": True,
            },
            "ocr_page": None,
            "expected_requested": True,
            "expected_status": OcrStatus.MISSING,
        },
        {
            "name": "empty image list",
            "baseline_page": {
                "needs_ocr": True,
            },
            "ocr_page": {
                "images": [],
            },
            "expected_requested": True,
            "expected_status": OcrStatus.EMPTY,
        },
        {
            "name": "OCR returned no text",
            "baseline_page": {
                "needs_ocr": True,
            },
            "ocr_page": {
                "images": [
                    {
                        "image": "page-1.png",
                        "lines": [],
                    }
                ],
            },
            "expected_requested": True,
            "expected_status": OcrStatus.EMPTY,
        },
        {
            "name": "OCR succeeded",
            "baseline_page": {
                "needs_ocr": True,
            },
            "ocr_page": {
                "images": [
                    {
                        "image": "page-1.png",
                        "lines": [
                            {
                                "text": "Recognized text",
                                "score": 0.98,
                            }
                        ],
                    }
                ],
            },
            "expected_requested": True,
            "expected_status": OcrStatus.SUCCEEDED,
        },
        {
            "name": "all images failed",
            "baseline_page": {
                "needs_ocr": True,
            },
            "ocr_page": {
                "images": [
                    {
                        "image": "page-1.png",
                        "error": "Image not found",
                    },
                    {
                        "image": "page-2.png",
                        "error": "OCR failed",
                    },
                ],
            },
            "expected_requested": True,
            "expected_status": OcrStatus.FAILED,
        },
        {
            "name": "some images failed",
            "baseline_page": {
                "needs_ocr": True,
            },
            "ocr_page": {
                "images": [
                    {
                        "image": "page-1.png",
                        "error": "Image not found",
                    },
                    {
                        "image": "page-2.png",
                        "lines": [
                            {
                                "text": "Recognized text",
                                "score": 0.91,
                            }
                        ],
                    },
                ],
            },
            "expected_requested": True,
            "expected_status": OcrStatus.PARTIAL_ERROR,
        },
    ]

    for case in test_cases:
        diagnostics = map_ocr_diagnostics(
            baseline_page=case["baseline_page"],
            ocr_page=case["ocr_page"],
        )

        assert diagnostics.ocr_requested is case[
            "expected_requested"
        ], (
            f"{case['name']}: "
            f"expected ocr_requested="
            f"{case['expected_requested']}, "
            f"got {diagnostics.ocr_requested}"
        )

        assert diagnostics.ocr_status is case[
            "expected_status"
        ], (
            f"{case['name']}: "
            f"expected status="
            f"{case['expected_status']}, "
            f"got {diagnostics.ocr_status}"
        ) 