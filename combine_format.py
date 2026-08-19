from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

from PDF_JSON_Fix import fix_pdf_json

BUILDER_VERSION = "0.3.0"
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
    section_path: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class SegmentDiagnostics:
    # 处理内容时出现的问题

    ocr_requested: bool
    ocr_status: OcrStatus

    dropped_duplicate_ocr_lines: int = 0
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


class FormattedDocumentBuilder:
    """Load parser/OCR artifacts and expose canonical documents only."""

    def __init__(
        self,
        *,
        output_dir: str | Path,
        baseline_file: str | Path,
        ocr_file: str | Path,
        source_dir: str | Path | None = None,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._baseline_file = Path(baseline_file)
        self._ocr_file = Path(ocr_file)
        self._source_dir = (
            Path(source_dir)
            if source_dir is not None
            else self._output_dir.parent.parent / "PDF_Folder"
        )

    def build(self) -> tuple[CanonicalDocument, ...]:
        baseline_report = self._read_json(self._baseline_file)
        ocr_report = self._read_json(self._ocr_file)
        baseline_documents = baseline_report.get("documents")

        if not isinstance(baseline_documents, dict):
            raise ValueError("Baseline report must contain a documents object.")

        ocr_documents = ocr_report.get("document", {})
        if not isinstance(ocr_documents, dict):
            raise ValueError("OCR report document field must be an object.")

        documents: list[CanonicalDocument] = []

        for document_name, baseline_document in baseline_documents.items():
            if not isinstance(document_name, str) or not isinstance(
                baseline_document, dict
            ):
                raise ValueError("Invalid baseline document entry.")

            raw_path = self._resolve_raw_path(document_name, baseline_document)
            raw_document = self._read_json(raw_path)
            source_name = baseline_document.get("source_pdf")

            if not isinstance(source_name, str) or not source_name:
                raise ValueError(
                    f"Baseline document {document_name!r} has no source_pdf."
                )

            fixed_json = fix_pdf_json(
                raw_document,
                source_name=source_name,
            )
            raw_document = fixed_json.document

            source_path = self._source_dir / source_name
            if not source_path.is_file():
                raise FileNotFoundError(f"Source PDF does not exist: {source_path}")

            content_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
            document_id = self._document_id(document_name, content_sha256)
            source = SourceReference(
                kind=SourceKind.PDF,
                source_name=source_name,
                source_uri=str(source_path),
                mime_type="application/pdf",
                content_sha256=content_sha256,
                title=fixed_json.title,
                page_count=int(baseline_document["page_count"]),
            )
            documents.append(
                build_canonical_document(
                    raw_document=raw_document,
                    baseline_document=baseline_document,
                    ocr_document=ocr_documents.get(document_name),
                    document_id=document_id,
                    source=source,
                    ignored_page_numbers=fixed_json.suppressed_pages,
                )
            )

        return tuple(documents)

    def _resolve_raw_path(
        self,
        document_name: str,
        baseline_document: dict[str, Any],
    ) -> Path:
        local_path = self._output_dir / f"{document_name}.json"
        if local_path.is_file():
            return local_path

        recorded_path = baseline_document.get("source_json")
        if isinstance(recorded_path, str) and Path(recorded_path).is_file():
            return Path(recorded_path)

        raise FileNotFoundError(
            f"Raw parser JSON does not exist for {document_name!r}."
        )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"Expected a JSON object in {path}.")
        return value

    @staticmethod
    def _document_id(document_name: str, content_sha256: str) -> str:
        slug = re.sub(r"[^\w]+", "-", document_name.casefold()).strip("-")
        return f"{slug or 'document'}-{content_sha256[:12]}"


# 基于raw_document / baseline 分析 构造 connonical
def build_canonical_document(
    raw_document,       # from opendataloader   
    baseline_document,  # from schema to classift document need ocr
    ocr_document,        # ocr result
    document_id,
    source:SourceReference,
    ignored_page_numbers: tuple[int, ...] = (),
):
    
    # 初始版本的Canonical document, 进入llm总结的最终版本
    page_count =  int(raw_document["number of pages"])     # opendataloader 结果中的page number
    
    if page_count != int(baseline_document["page_count"]):
        raise ValueError("Raw document and baseline page counts do not match.")

    if source.page_count is not None and source.page_count != page_count:
        raise ValueError("SourceReference page count does not match raw document.")
    
    baseline_pages = baseline_document["pages"] #???????
    ocr_pages = (ocr_document or {}).get("pages", {})   # 已经ocr完成的
    ignored_pages = set(ignored_page_numbers)

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

        if page_number in ignored_pages:
            merged_blocks = ()
            diagnostics = replace(
                diagnostics,
                warnings=(
                    *diagnostics.warnings,
                    "Page excluded from LLM content by PDF_JSON_Fix.",
                ),
            )
        else:
            merged_blocks, diagnostics = merge_page_blocks(
                native_blocks=native_blocks,
                ocr_page=ocr_pages.get(page_key),
                document_id=document_id,
                page_number=page_number,
                diagnostics=diagnostics,
            )

        # document build
        segments.append(
            CanonicalSegment(
                segment_id = f"{document_id}:page:{page_number}",
                ordinal = page_number -1,
                locator = PdfPageLocator(page_number=page_number),
                content=render_page_content(merged_blocks),
                blocks=merged_blocks,
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
def _iter_native_nodes(
    value: Any,
    inside_table: bool = False,
) -> Iterator[dict[str, Any]]:
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
    section_stack: dict[int, str] = {}

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
            pdfua_tag = node.get("pdfua_tag")
            heading_match = (
                re.fullmatch(r"H([1-6])", pdfua_tag)
                if isinstance(pdfua_tag, str)
                else None
            )
            if heading_match:
                heading_rank = int(heading_match.group(1))
            elif node.get("level") in {"Doctitle", "Title"}:
                heading_rank = 1

        if heading_rank is not None:
            section_stack = {
                rank: heading
                for rank, heading in section_stack.items()
                if rank < heading_rank
            }
            section_stack[heading_rank] = text

        section_path = tuple(
            section_stack[rank]
            for rank in sorted(section_stack)
        )

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
                section_path=section_path,
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
        if block.type is not BlockType.FIGURE or not block.asset_ref:
            continue

        figures_by_asset[_normalize_asset_ref(block.asset_ref)] = block

    matches: list[tuple[ContentBlock, dict[str, Any]]] = []
    unmatched_ocr_images: list[str] = []
    matched_assets: set[str] = set()

    for image_result in (ocr_page or {}).get("images", ()):
        if not isinstance(image_result, dict):
            continue

        image_ref = image_result.get("image")
        if not isinstance(image_ref, str) or not image_ref.strip():
            continue

        normalized_ref = _normalize_asset_ref(image_ref)
        native_figure = figures_by_asset.get(normalized_ref)

        if native_figure is None:
            unmatched_ocr_images.append(image_ref)
            continue

        matches.append((native_figure, image_result))
        matched_assets.add(normalized_ref)

    missing_ocr_images = [
        block.asset_ref
        for normalized_ref, block in figures_by_asset.items()
        if normalized_ref not in matched_assets and block.asset_ref is not None
    ]

    return OcrImageMatchResult(
        matches=tuple(matches),
        unmatched_ocr_images=tuple(unmatched_ocr_images),
        missing_ocr_images=tuple(missing_ocr_images),
    )


def _normalized_text(text: str) -> str:
    """Return a conservative comparison form for OCR de-duplication."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\W+", "", normalized, flags=re.UNICODE)


def _duplicates_existing_text(candidate: str, existing_texts: set[str]) -> bool:
    normalized = _normalized_text(candidate)

    if not normalized:
        return True

    for existing in existing_texts:
        if normalized == existing:
            return True

        if min(len(normalized), len(existing)) >= 8 and (
            normalized in existing or existing in normalized
        ):
            return True

    return False


def _ocr_blocks_for_image(
    image_result: dict[str, Any],
    *,
    figure: ContentBlock | None,
    document_id: str,
    page_number: int,
    existing_texts: set[str],
    next_ocr_index: int,
    section_path: tuple[str, ...],
) -> tuple[list[ContentBlock], int, int]:
    blocks: list[ContentBlock] = []
    dropped_duplicates = 0
    image_ref = image_result.get("image")

    for line in image_result.get("lines", ()):
        if not isinstance(line, dict):
            continue

        raw_text = line.get("text")
        text = raw_text.strip() if isinstance(raw_text, str) else ""

        if not text:
            continue

        if _duplicates_existing_text(text, existing_texts):
            dropped_duplicates += 1
            continue

        normalized = _normalized_text(text)
        existing_texts.add(normalized)

        raw_score = line.get("score")
        confidence = (
            float(raw_score)
            if isinstance(raw_score, (int, float))
            else None
        )

        blocks.append(
            ContentBlock(
                block_id=(
                    f"{document_id}:page:{page_number}:ocr:{next_ocr_index}"
                ),
                ordinal=-1,
                type=BlockType.PARAGRAPH,
                source=ContentSource.OCR,
                text=text,
                bounding_box=(figure.bounding_box if figure else None),
                asset_ref=(
                    image_ref if isinstance(image_ref, str) else None
                ),
                confidence=confidence,
                section_path=section_path,
            )
        )
        next_ocr_index += 1

    return blocks, next_ocr_index, dropped_duplicates


def merge_page_blocks(
    *,
    native_blocks: tuple[ContentBlock, ...],
    ocr_page: dict[str, Any] | None,
    document_id: str,
    page_number: int,
    diagnostics: SegmentDiagnostics,
) -> tuple[tuple[ContentBlock, ...], SegmentDiagnostics]:
    """Merge OCR supplements into native reading order for one page."""

    match_result = match_ocr_images(native_blocks, ocr_page)
    images_by_figure = {
        figure.block_id: image_result
        for figure, image_result in match_result.matches
    }
    existing_texts = {
        normalized
        for block in native_blocks
        if (normalized := _normalized_text(block.text))
    }
    merged: list[ContentBlock] = []
    next_ocr_index = 0
    dropped_duplicates = 0

    for native_block in native_blocks:
        merged.append(native_block)
        image_result = images_by_figure.get(native_block.block_id)

        if image_result is None:
            continue

        ocr_blocks, next_ocr_index, dropped = _ocr_blocks_for_image(
            image_result,
            figure=native_block,
            document_id=document_id,
            page_number=page_number,
            existing_texts=existing_texts,
            next_ocr_index=next_ocr_index,
            section_path=native_block.section_path,
        )
        merged.extend(ocr_blocks)
        dropped_duplicates += dropped

    matched_image_ids = {id(image) for _, image in match_result.matches}

    for image_result in (ocr_page or {}).get("images", ()):
        if (
            not isinstance(image_result, dict)
            or id(image_result) in matched_image_ids
        ):
            continue

        ocr_blocks, next_ocr_index, dropped = _ocr_blocks_for_image(
            image_result,
            figure=None,
            document_id=document_id,
            page_number=page_number,
            existing_texts=existing_texts,
            next_ocr_index=next_ocr_index,
            section_path=(
                native_blocks[-1].section_path if native_blocks else ()
            ),
        )
        merged.extend(ocr_blocks)
        dropped_duplicates += dropped

    warnings = list(diagnostics.warnings)
    if match_result.unmatched_ocr_images:
        warnings.append("OCR results were not matched to native figures.")
    if ocr_page is not None and match_result.missing_ocr_images:
        warnings.append("Native figures were missing OCR results.")

    ordered_blocks = tuple(
        replace(block, ordinal=ordinal)
        for ordinal, block in enumerate(merged)
    )
    updated_diagnostics = replace(
        diagnostics,
        dropped_duplicate_ocr_lines=dropped_duplicates,
        unmatched_ocr_images=match_result.unmatched_ocr_images,
        warnings=tuple(warnings),
    )
    return ordered_blocks, updated_diagnostics


def render_page_content(blocks: tuple[ContentBlock, ...]) -> str:
    """Render the one canonical text representation consumed downstream."""

    parts: list[str] = []

    for block in blocks:
        if not block.text:
            continue

        if block.type is BlockType.HEADING and block.heading_rank is not None:
            parts.append(f"{'#' * min(block.heading_rank, 6)} {block.text}")
        else:
            parts.append(block.text)

    return "\n\n".join(parts)
