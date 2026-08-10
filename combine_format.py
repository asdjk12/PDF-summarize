from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum # 固定格式，避免修改
from collections.abc import Iterator
from typing import Any

BUILDER_VERSION = "0.1.0"
MERGE_STRATEGY = "native_first_ocr_supplement"

#*******************Fixed Class*******************
class SourceKind(StrEnum):
    # 文档类型
    PDF = "pdf"

class LocatorKind(StrEnum):
    PDF_PAGE = "pdf_page"

class BlockType(StrEnum):
    # ocr 识别block的信息
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    CAPTION = "caption"
    TABLE = "table"
    FORMULA = "formula"
    FIGURE = "figure"

class ContentSource(StrEnum):
    NATIVE = "native"   # opendataloader
    OCR = "ocr"   
    VISION = "vision"   # 音频，未来计划做****  

class OcrStatus(StrEnum):
    NOT_REQUESTED = "not_requested"
    SUCCEEDED = "succeeded"
    EMPTY = "empty"
    MISSING = "missing"
    PARTIAL_ERROR = "partial_error"
    FAILED = "failed"

#*******************dataclass*******************
@dataclass(frozen=True, slots=True)
class CanonicalDocument:
    # 最高level， 唯一对外形式
    """
    Task:
        遍历 OpenDataLoader 数据
        恢复内容顺序
        识别内容类型
        匹配 OCR 图片
        合并 native/OCR
        去除重复 OCR
        构造唯一 content
        生成诊断信息
        返回 CanonicalDocument
    """
    document_id: str
    source: SourceReference
    segments: tuple[CanonicalSegment, ...]

    builder_version: str
    merge_strategy: str

    # schema iteration
    schema_version: str = field(
        default="1.0",
        init=False,
    )

@dataclass(frozen=True, slots=True)
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float

@dataclass(frozen=True, slots=True)
class SourceReference:
    # 原始文件
    """
    SourceReference(
        kind=SourceKind.PDF,
        source_name="Week 2 - Language Modelling-CL-2026.pdf",
        source_uri="PDF_Folder/Week 2 - Language Modelling-CL-2026.pdf",
        mime_type="application/pdf",
        content_sha256="abc123...",
        title="Language Modelling",
        languages=("en",),
        page_count=74,
    )
    """
    kind: SourceKind
    source_name: str
    source_uri: str
    mime_type:str          # ???????
    content_sha256: str     # private key

    title: str | None = None
    languages: tuple[str, ...] = ()
    page_count: int | None = None

@dataclass(frozen=True, slots=True)
class PdfPageLocator:
    # 表示 segment 来自 PDF 的哪一页
    page_number: int

    kind: LocatorKind = field(
        default=LocatorKind.PDF_PAGE,
        init=False,
    )

# ============================================================
# Canonical content model
# ============================================================

@dataclass(frozen=True, slots=True)
class ContentBlock:
    # 最小内容块
    """
        - one heading
        - one paragraph
        - one list item
        - one Markdown table
        - one formula
        - one figure
    """
    block_id: str
    ordinal: int
    type: BlockType
    source: ContentSource

    text: str
    bounding_box: BoundingBox | None
    heading_rank: int | None = None

    # 图片或公式原图的路径
    asset_ref: str | None = None

    # OCR 或视觉识别置信度
    confidence: float | None = None

@dataclass(frozen=True, slots=True)
class SegmentDiagnostics:
    # 处理内容时出现的问题

    ocr_requested: bool
    ocr_status: OcrStatus

    # dropped_duplicate_ocr_lines: int = 0 
    unmatched_ocr_images: tuple[str, ...] = ()  # 异常未匹配page， 便于debug
    warnings: tuple[str, ...] = ()  

@dataclass(frozen=True, slots=True)
class CanonicalSegment:
    # 一个 segment 对应one page
    segment_id: str
    ordinal: int
    locator: PdfPageLocator
    content: str
    blocks: tuple[ContentBlock, ...]
    diagnostics: SegmentDiagnostics

@dataclass(frozen=True, slots=True)
class OcrImageMatchResult:
    """
    OCR 图片匹配的内部结果。
    """

    matches: tuple[
        tuple[ContentBlock, dict[str, Any]],
        ...,
    ]

    unmatched_ocr_images: tuple[str, ...]
    missing_ocr_images: tuple[str, ...]


"""
def build():
    # 主要构造入口
    
    OpenDataLoader JSON
    + baseline_analysis.json
    + ocr_results.json
    
    每页输出唯一 content, 同时保留有序 blocks。
    原生结构为主, OCR 只补充图片文字并去重。
    直接替换旧接口和旧 JSON, 不保留 extracted_text/ocr_text 双格式。
    本轮止于 canonical document, 不实现切块、LLM 调用和摘要展示。
    """

NATIVE_BLOCK_TYPES = {
    # block 的最初版本
    "heading": BlockType.HEADING,
    "paragraph": BlockType.PARAGRAPH,
    "list item": BlockType.LIST_ITEM,
    "caption": BlockType.CAPTION,
    "table": BlockType.TABLE,
    "image": BlockType.FIGURE,
    "formula": BlockType.FORMULA,
}


# 基于raw_document / baseline 分析 构造 connonical
def build_canonical_document(
    raw_document,       # from opendataloader   
    baseline_document,  # from schema to classift document need ocr
    ocr_document,        # ocr result
    document_id,
    source:SourceReference,
):
    
    # 初始版本的Canonical document, 进入llm总结的最终版本
    page_count =  int(raw_document["number of pages"])     # opendataloader 结果中的page number
    
    if page_count != int(baseline_document["page_count"]):
        raise ValueError("Raw document and baseline page counts do not match.")

    if source.page_count is not None and source.page_count != page_count:
        raise ValueError("SourceReference page count does not match raw document.")
    
    baseline_pages = baseline_document["pages"] #???????
    ocr_pages = (ocr_document or {}).get("pages", {})   # 已经ocr完成的

    segments = []   
    native_blocks_by_page = extract_native_blocks(
        raw_document,
        document_id=document_id,
    )

    for page_number in range(1, page_count + 1):
        page_key = str(page_number)

        # ocr status setup     
        diagnostics = map_ocr_diagnostics(
            baseline_page=baseline_pages[page_key],
            ocr_page=ocr_pages.get(page_key),
        )

        # 构造初始版blocks
        native_blocks = native_blocks_by_page.get(
            page_number,
            (),
        )

        # document build
        segments.append(
            CanonicalSegment(
                segment_id = f"{document_id}:page:{page_number}",
                ordinal = page_number -1,
                locator = PdfPageLocator(page_number=page_number),
                content="",
                blocks=native_blocks,
                diagnostics=diagnostics         # diagnostics
            )
        )

    return CanonicalDocument(
        document_id=document_id,
        source=source,
        segments=tuple(segments),
        builder_version=BUILDER_VERSION,  # global variable, iteration
        merge_strategy=MERGE_STRATEGY,      # ~
    )

"""
    From codex: start
"""
def _iter_native_nodes(value, inside_table:bool = False):
    # opendataloader 的节点遍历，为了构造contentBlock 节点
    if isinstance(value, list):
        # list 情况
        for item in value:
            yield from _iter_native_nodes(
                item,
                inside_table=inside_table,
            )
        return

    if not isinstance(value, dict):
        # dict 情况
        return
    
    node_type = value.get("type")

    if node_type == "table":
        # 整张表只生成一个 TABLE block。
        yield value
        inside_table = True

    elif node_type == "image":
        # 表格内部的图片不能丢失，仍然生成 FIGURE block。
        yield value

    elif not inside_table and node_type in NATIVE_BLOCK_TYPES:
        yield value

    # OpenDataLoader 当前实际使用的结构子节点。
    for child_key in ("kids", "list items", "rows", "cells"):
        yield from _iter_native_nodes(
            value.get(child_key, ()),
            inside_table=inside_table,
        )

def _table_to_markdown(table_node: dict[str, Any]) -> str:
    """把 OpenDataLoader table node 转为简单 Markdown table。"""

    def cell_text(value: Any) -> str:
        parts: list[str] = []

        def collect(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    collect(item)
                return

            if not isinstance(node, dict):
                return

            content = node.get("content")

            if isinstance(content, str) and content.strip():
                parts.append(content.strip())

            for child_key in ("kids", "list items"):
                collect(node.get(child_key, ()))

        collect(value)

        return (
            " ".join(parts)
            .replace("\n", " ")
            .replace("|", r"\|")
        )

    rows = [
        [cell_text(cell) for cell in row.get("cells", ())]
        for row in table_node.get("rows", ())
    ]

    rows = [row for row in rows if row]

    if not rows:
        return ""

    column_count = max(len(row) for row in rows)

    # 不擅自把第一行判断成表头，使用中性列名。
    header = [
        f"column_{index}"
        for index in range(1, column_count + 1)
    ]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]

    for row in rows:
        padded_row = row + [""] * (column_count - len(row))
        lines.append("| " + " | ".join(padded_row) + " |")

    return "\n".join(lines)
"""
codex: END
"""

def extract_native_blocks(
    raw_document,
    document_id,    
):
    # 从openDataLoader结果中 解析并映射 至native_block
    """
    return:
        {
            1: (block_1, block_2, ...),
            2: (...),
        }
    """

    blocks_by_page: dict[int, list[ContentBlock]] = {}  

    for node in _iter_native_nodes(raw_document):
        page_number = node.get("page number")   # get page

        # break 

        if not isinstance(page_number, int): 
            continue

        node_type = node.get("type")
        block_type = NATIVE_BLOCK_TYPES[node_type]

        if block_type is BlockType.TABLE:
            # 表格读取
            text = _table_to_markdown(node)
        else:
            # 文字读取
            raw_text = node.get("content", "")
            text = raw_text.strip() if isinstance(raw_text, str) else ""

        # 图片没有文字也必须保留；其他空节点没有检索价值。
        if not text and block_type is not BlockType.FIGURE:
            continue

        raw_box = node.get("bounding box")

        bounding_box = (
            BoundingBox(*(float(value) for value in raw_box))
            if isinstance(raw_box, list) and len(raw_box) == 4
            else None
        )

        heading_rank = None

        if block_type is BlockType.HEADING:
            heading_rank = {
                "Doctitle": 1,
                "Title": 1,
                "Subtitle": 2,
            }.get(node.get("level"))

        page_blocks = blocks_by_page.setdefault(page_number, [])
        ordinal = len(page_blocks)

        page_blocks.append(
            ContentBlock(
                block_id=(
                    f"{document_id}:page:{page_number}"
                    f":native:{ordinal}"
                ),
                ordinal=ordinal,
                type=block_type,
                source=ContentSource.NATIVE,
                text=text,
                bounding_box=bounding_box,
                heading_rank=heading_rank,
                asset_ref=(
                    node.get("source")
                    if block_type is BlockType.FIGURE
                    else None
                ),
                confidence=None,
            )
        )
    return {
        page_number: tuple(blocks)
        for page_number, blocks in blocks_by_page.items()
    }

def map_ocr_diagnostics(
    baseline_page,
    ocr_page,      
)-> SegmentDiagnostics:
    """
    Convert page result into SegmentDiagnostics

    baseline	    OCR 数据	            状态
    不需要 OCR	       无	               NOT_REQUESTED
    需要 OCR	       有图片、有识别行	    SUCCEEDED
    需要 OCR	       OCR 执行完成但无行	EMPTY
    需要 OCR	       OCR 报告中没有该页   MISSING
    多张图片部分成功	部分错误	        PARTIAL_ERROR
    全部图片错误	    全部失败	        FAILED
    """
    # ===============
    # Phase 1: 先确认是否需要ocr
    # ===============
    ocr_requested = bool(
        baseline_page.get("needs_ocr")
    )

    if not ocr_requested: # no
        return SegmentDiagnostics(
            ocr_requested=False,
            ocr_status= OcrStatus.NOT_REQUESTED
        )

    # ===============
    # Phase 2: ocr需求结果确认后
    #                   ocr_page 状态
    # ===============

    # ocr_page None && ocr_requested Yes
    if ocr_page is None:
        return SegmentDiagnostics(
            ocr_requested=True,
            ocr_status=OcrStatus.MISSING,   # 应该 OCR，但 ocr_document["pages"] 里根本没有这一页
        )

    # 有images
    images = ocr_page.get("images", [])

    # ===============
    # Phase 3: ocr需求结果 和 ocr_page 状态确认后
    #              获取image 读取结果
    # ===============

    if not isinstance(images, list) or not images:
        return SegmentDiagnostics(
            ocr_requested=True,
            ocr_status=OcrStatus.EMPTY,     # OCR运行，但没有识别出图片中的有效文字
        )     

    # 图片结果
    image_results = [
        image
        for image in images
        if isinstance(image, dict)
    ]

    if not image_results:
        return SegmentDiagnostics(
            ocr_requested=True,
            ocr_status=OcrStatus.EMPTY,
        )

    # error
    error_count = sum(
        bool(image.get("error"))
        for image in image_results
    )

    # 全部失败
    if error_count == len(image_results):
        ocr_status = OcrStatus.FAILED   

    # 部分失败
    elif error_count > 0:
        ocr_status = OcrStatus.PARTIAL_ERROR

    else:
        has_text = any(
            isinstance(line, dict)
            and isinstance(line.get("text"), str)
            and bool(line["text"].strip())
            for image in image_results
            for line in image.get("lines", [])
        )

        ocr_status = (
            OcrStatus.SUCCEEDED
            if has_text
            else OcrStatus.EMPTY
        )

    return SegmentDiagnostics(
        ocr_requested=True,
        ocr_status=ocr_status,
    )

def match_ocr_images(
    native_blocks: tuple[ContentBlock, ...],
    ocr_page: dict[str, Any] | None,
) -> OcrImageMatchResult:
    """
    将当前页 OCR 图片结果匹配到 native FIGURE block。

    匹配键：
        ContentBlock.asset_ref
        ==
        OCR image result["image"]
    """

    def _normalize_asset_ref(asset_ref: str) -> str:
        """
        标准化图片相对路径。
        """

        normalized = asset_ref.strip().replace("\\", "/")

        if normalized.startswith("./"):
            normalized = normalized[2:]

        return normalized

    figures_by_asset: dict[str, ContentBlock] = {}

    for block in native_blocks:


    