"""Normalize OpenDataLoader JSON before Canonical construction.

The module uses deterministic text and page-structure rules. It does not run
OCR and does not inspect the original PDF layout.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PDFJSONFixResult:
    """Cleaned parser JSON plus document-level normalization decisions."""

    document: dict[str, Any]
    suppressed_pages: tuple[int, ...]
    title: str


class PDFJSONFixer:
    """Apply document-wide cleanup while preserving the parser JSON shape."""

    _INCOMPLETE_ENDINGS = frozenset(
        {
            "a",
            "an",
            "and",
            "for",
            "in",
            "of",
            "on",
            "or",
            "the",
            "to",
            "with",
        }
    )

    def fix(
        self,
        raw_document: dict[str, Any],
        *,
        source_name: str,
    ) -> PDFJSONFixResult:
        page_nodes = self._collect_page_nodes(raw_document)
        suppressed_pages = self._repeated_overview_pages(page_nodes)
        suppressed_pages.update(self._course_feedback_pages(page_nodes))
        fixed_document = self._transform(raw_document, suppressed_pages)
        title = self._resolve_title(raw_document.get("title"), source_name)
        fixed_document["title"] = title

        return PDFJSONFixResult(
            document=fixed_document,
            suppressed_pages=tuple(sorted(suppressed_pages)),
            title=title,
        )

    def _collect_page_nodes(
        self,
        value: Any,
    ) -> dict[int, list[dict[str, Any]]]:
        nodes: dict[int, list[dict[str, Any]]] = defaultdict(list)

        def collect(item: Any) -> None:
            if isinstance(item, list):
                for child in item:
                    collect(child)
                return
            if not isinstance(item, dict):
                return

            page_number = item.get("page number")
            if isinstance(page_number, int) and isinstance(
                item.get("type"),
                str,
            ):
                nodes[page_number].append(item)

            for child_key in ("kids", "list items", "rows", "cells"):
                collect(item.get(child_key, ()))

        collect(value)
        return dict(nodes)

    def _repeated_overview_pages(
        self,
        page_nodes: dict[int, list[dict[str, Any]]],
    ) -> set[int]:
        seen_fingerprints: set[tuple[tuple[str, str], ...]] = set()
        suppressed: set[int] = set()

        for page_number in sorted(page_nodes):
            nodes = page_nodes[page_number]
            has_overview_heading = any(
                node.get("type") == "heading"
                and self._normalized_text(node.get("content")) == "overview"
                for node in nodes
            )
            if not has_overview_heading:
                continue

            fingerprint = tuple(
                (
                    str(node.get("type", "")),
                    self._normalized_text(node.get("content")),
                )
                for node in nodes
                if self._normalized_text(node.get("content"))
            )
            if fingerprint in seen_fingerprints:
                suppressed.add(page_number)
            else:
                seen_fingerprints.add(fingerprint)

        return suppressed

    def _course_feedback_pages(
        self,
        page_nodes: dict[int, list[dict[str, Any]]],
    ) -> set[int]:
        suppressed: set[int] = set()

        for page_number, nodes in page_nodes.items():
            texts = [self._normalized_text(node.get("content")) for node in nodes]
            has_feedback_heading = any(
                re.fullmatch(r"feedback\s+time!?", text)
                for text in texts
            )
            has_weekly_submission = any(
                "submit weekly feedback" in text
                for text in texts
            )
            if has_feedback_heading and has_weekly_submission:
                suppressed.add(page_number)

        return suppressed

    def _transform(
        self,
        value: Any,
        suppressed_pages: set[int],
    ) -> Any:
        if isinstance(value, list):
            transformed = [
                self._transform(item, suppressed_pages)
                for item in value
            ]
            return [item for item in transformed if item is not None]

        if not isinstance(value, dict):
            return value

        if value.get("page number") in suppressed_pages:
            return None

        transformed = {
            key: self._transform(item, suppressed_pages)
            for key, item in value.items()
        }
        if transformed.get("type") != "heading":
            return transformed

        text = transformed.get("content")
        normalized = self._normalized_text(text)
        if not any(character.isalnum() for character in normalized):
            return None

        if normalized == "overview" or self._looks_incomplete_heading(normalized):
            transformed["type"] = "paragraph"

        return transformed

    def _looks_incomplete_heading(self, normalized: str) -> bool:
        words = re.findall(r"[\w-]+", normalized, flags=re.UNICODE)
        return (
            len(normalized) > 80
            and bool(words)
            and words[-1] in self._INCOMPLETE_ENDINGS
        )

    @staticmethod
    def _resolve_title(raw_title: Any, source_name: str) -> str:
        title = raw_title.strip() if isinstance(raw_title, str) else ""
        is_generic_course_code = bool(
            re.fullmatch(r"[A-Za-z]{2,}\s*\d{3,}", title)
        )
        if title and not is_generic_course_code:
            return title
        return Path(source_name).stem

    @staticmethod
    def _normalized_text(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        normalized = unicodedata.normalize("NFKC", value).casefold()
        return re.sub(r"\s+", " ", normalized).strip()


def fix_pdf_json(
    raw_document: dict[str, Any],
    *,
    source_name: str,
) -> PDFJSONFixResult:
    """Return parser JSON normalized for the Canonical/Chunk pipeline."""

    return PDFJSONFixer().fix(raw_document, source_name=source_name)
