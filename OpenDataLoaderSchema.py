from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ANALYSIS_VERSION = 1
OCR_TEXT_CHAR_THRESHOLD = 80
OCR_LARGE_IMAGE_TEXT_CHAR_THRESHOLD = 150
OCR_LARGE_IMAGE_AREA_THRESHOLD = 50_000


class OpenDataLoaderSchema:
    # open data loader 的输出结构
    FILE_NAME = "file name"
    PAGE_COUNT = "number of pages"
    PAGE_NUMBER = "page number"
    CONTENT = "content"
    NODE_TYPE = "type"
    IMAGE_TYPE = "image"
    SOURCE = "source"
    BOUNDING_BOX = "bounding box"


@dataclass(frozen=True)
class OcrPolicy:
    text_char_threshold: int = OCR_TEXT_CHAR_THRESHOLD
    large_image_text_char_threshold: int = OCR_LARGE_IMAGE_TEXT_CHAR_THRESHOLD
    large_image_area_threshold: float = OCR_LARGE_IMAGE_AREA_THRESHOLD

    def decide(self, page: "PageSignals") -> list[str]:
        if page.image_count == 0:   # 无图片情况
            return []
        
        # 按照优先级命中
        ordered_checks = (
            (page.text_chars == 0, "no extracted text but has image"),
            (
                page.text_chars < self.text_char_threshold,
                "very little extracted text and has image",
            ),
            (
                page.text_chars < self.large_image_text_char_threshold
                and page.largest_image_area > self.large_image_area_threshold,
                "little extracted text and has large image",
            ),
        )

        for is_match, reason in ordered_checks:
            if is_match:
                return [reason]

        return []

    def thresholds(self) -> dict[str, int | float]:
        return {
            "ocr_text_char_threshold": self.text_char_threshold,
            "ocr_large_image_text_char_threshold": self.large_image_text_char_threshold,
            "ocr_large_image_area_threshold": self.large_image_area_threshold,
        }


@dataclass
class PageSignals:
    # ppt中单页的信息

    text_chars: int = 0
    text_nodes: int = 0
    image_count: int = 0
    largest_image_area: float = 0
    image_sources: list[str] = field(default_factory=list)

    @classmethod
    def from_nodes(cls, nodes: Iterable[dict[str, Any]]) -> "PageSignals":
        page = cls()
        for node in nodes:
            page.capture(node)
        return page

    def capture(self, node: dict[str, Any]) -> None:
        content = node.get(OpenDataLoaderSchema.CONTENT)
        if isinstance(content, str):
            stripped_content = content.strip()
            if stripped_content:
                self.text_chars += len(stripped_content)
                self.text_nodes += 1

        if node.get(OpenDataLoaderSchema.NODE_TYPE) != OpenDataLoaderSchema.IMAGE_TYPE:
            return

        self.image_count += 1

        source = node.get(OpenDataLoaderSchema.SOURCE)
        if isinstance(source, str) and source:
            self.image_sources.append(source)

        self.largest_image_area = max(
            self.largest_image_area,
            self._bounding_box_area(node.get(OpenDataLoaderSchema.BOUNDING_BOX)),
        )

    def to_report(self, reasons: list[str]) -> dict[str, Any]:
        return {
            "needs_ocr": bool(reasons),
            "reasons": reasons,
            "text_chars": self.text_chars,
            "text_nodes": self.text_nodes,
            "image_count": self.image_count,
            "largest_image_area": round(self.largest_image_area, 2),
            "image_sources": self.image_sources,
        }

    @staticmethod
    def _bounding_box_area(bounding_box: Any) -> float:
        if not isinstance(bounding_box, list) or len(bounding_box) != 4:
            return 0

        try:
            x1, y1, x2, y2 = (float(value) for value in bounding_box)
        except (TypeError, ValueError):
            return 0

        return max(0, x2 - x1) * max(0, y2 - y1)


@dataclass(frozen=True)
class BaselineAnalyzer:
    # 页级 OCR 判断
    output_dir: Path        # 存放openDataLoader JSON输出结果的地方
    analysis_file: Path     # 存放 page OCR 前置分析的地方
    policy: OcrPolicy       # OCR policy

    def analyse(self) -> dict[str, Any]:
        report = {
            "analysis_version": ANALYSIS_VERSION,
            "thresholds": self.policy.thresholds(),
            "documents": {},
        }

        for json_file in self.source_json_files():
            document_data = json.loads(json_file.read_text(encoding="utf-8"))
            document_name = self.document_name(document_data, json_file)
            report["documents"][document_name] = self.analyse_document(
                document_data=document_data,
                json_file=json_file,
            )

        self.analysis_file.parent.mkdir(parents=True, exist_ok=True)
        self.analysis_file.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        for document_name, document_report in report["documents"].items():
            print(
                f"{document_name}: "
                f"{document_report['needs_ocr_page_count']}/"
                f"{document_report['page_count']} pages need OCR"
            )

        print(f"Baseline analysis completed; saved to: {self.analysis_file}")
        return report

    def source_json_files(self) -> list[Path]:

        if not self.output_dir.exists():
            raise FileNotFoundError(f"PDF output folder does not exist: {self.output_dir}")

        json_files = [
            json_file
            for json_file in sorted(self.output_dir.glob("*.json")) 
            if self.is_opendataloader_document_json(json_file)
        ]

        if not json_files:
            raise FileNotFoundError(
                f"No OpenDataLoader JSON files found in: {self.output_dir}"
            )

        return json_files

    def analyse_document(
        self,
        document_data: dict[str, Any],
        json_file: Path,
    ) -> dict[str, Any]:
        page_nodes = self.nodes_by_page(document_data)
        page_count = self.page_count(document_data)
        pages = {}
        needs_ocr_pages = []

        for page_number in range(1, page_count + 1):
            page = PageSignals.from_nodes(page_nodes.get(page_number, ()))
            page_report = page.to_report(self.policy.decide(page))
            pages[str(page_number)] = page_report

            if page_report["needs_ocr"]:
                needs_ocr_pages.append(page_number)

        return {
            "source_json": str(json_file),
            "source_pdf": document_data.get(OpenDataLoaderSchema.FILE_NAME),
            "page_count": page_count,
            "needs_ocr_pages": needs_ocr_pages,
            "needs_ocr_page_count": len(needs_ocr_pages),
            "pages": pages,
        }

    @staticmethod
    def document_name(document_data: dict[str, Any], json_file: Path) -> str:
        source_pdf = document_data.get(OpenDataLoaderSchema.FILE_NAME)
        if isinstance(source_pdf, str) and source_pdf:
            return Path(source_pdf).stem
        return json_file.stem

    @staticmethod
    def page_count(document_data: dict[str, Any]) -> int:
        value = document_data.get(OpenDataLoaderSchema.PAGE_COUNT)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def nodes_by_page(document_data: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
        page_nodes = defaultdict(list)
        stack: list[Any] = [document_data]

        while stack:
            node = stack.pop()

            if isinstance(node, dict):
                page_number = node.get(OpenDataLoaderSchema.PAGE_NUMBER)
                if isinstance(page_number, int):
                    page_nodes[page_number].append(node)

                stack.extend(reversed(list(node.values())))

            elif isinstance(node, list):
                stack.extend(reversed(node))

        return dict(page_nodes)
    
    @staticmethod
    def is_opendataloader_document_json(json_file: Path) -> bool:
        # 用于过滤，确保只有pdf文档下的内容进入 baseline_analyzer
        try:
            document_data = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False

        if not isinstance(document_data, dict):
            return False

        source_pdf = document_data.get(OpenDataLoaderSchema.FILE_NAME)      # file_name 
        page_count = document_data.get(OpenDataLoaderSchema.PAGE_COUNT)     # page_no

        if not isinstance(source_pdf, str) or not source_pdf:
            return False

        try:
            return int(page_count) > 0
        except (TypeError, ValueError):
            return False


def baseline_analyse(
    output_dir: Path,
    analysis_file: Path,
    policy: OcrPolicy | None = None,
) -> dict[str, Any]:
    return BaselineAnalyzer(
        output_dir=output_dir,
        analysis_file=analysis_file,
        policy=policy if policy is not None else OcrPolicy(),
    ).analyse()


__all__ = [
    "ANALYSIS_VERSION",
    "BaselineAnalyzer",
    "OCR_LARGE_IMAGE_AREA_THRESHOLD",
    "OCR_LARGE_IMAGE_TEXT_CHAR_THRESHOLD",
    "OCR_TEXT_CHAR_THRESHOLD",
    "OcrPolicy",
    "OpenDataLoaderSchema",
    "PageSignals",
    "baseline_analyse",
]
