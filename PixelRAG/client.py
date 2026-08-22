"""PixelRAG HTTP response translation at the visual-retrieval seam."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from pdf_knowledge_agent.domain.knowledge import PdfPageLocator
from pdf_knowledge_agent.domain.visual_retrieval import (
    VisualSearchRequest,
    VisualSearchResult,
)


class PixelRagResponseError(RuntimeError):
    """Raised when PixelRAG is unavailable or returns an invalid result."""


class PixelRagTransport(Protocol):
    """Injectable JSON transport used by the client and its contract tests."""

    def __call__(
        self,
        endpoint: str,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class PixelRagDocument:
    """Explicit mapping between one project document and one indexed PDF."""

    document_id: str
    source_file: Path

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("PixelRAG document_id must not be blank.")
        selected_source = Path(self.source_file).resolve()
        if not selected_source.is_file():
            raise ValueError(
                f"PixelRAG source PDF does not exist: {selected_source}"
            )
        object.__setattr__(self, "source_file", selected_source)


class PixelRagSearchClient:
    """Hide PixelRAG's HTTP schema and return project-owned page results."""

    def __init__(
        self,
        endpoint: str,
        documents: tuple[PixelRagDocument, ...],
        vendor_working_directory: Path,
        *,
        timeout_seconds: float = 120.0,
        transport: PixelRagTransport | None = None,
    ) -> None:
        if not endpoint.strip():
            raise ValueError("PixelRAG endpoint must not be blank.")
        if not documents:
            raise ValueError("PixelRAG requires at least one document mapping.")
        if timeout_seconds <= 0:
            raise ValueError("PixelRAG timeout must be greater than zero.")

        document_ids = tuple(document.document_id for document in documents)
        if len(set(document_ids)) != len(document_ids):
            raise ValueError("PixelRAG document IDs must be unique.")

        self._endpoint = endpoint.rstrip("/")
        self._vendor_working_directory = Path(
            vendor_working_directory
        ).resolve()
        self._timeout_seconds = timeout_seconds
        self._transport = transport or _post_json
        self._documents_by_source = {
            _path_key(document.source_file): document.document_id
            for document in documents
        }
        if len(self._documents_by_source) != len(documents):
            raise ValueError("PixelRAG source PDF mappings must be unique.")

    def search(
        self,
        request: VisualSearchRequest,
    ) -> tuple[VisualSearchResult, ...]:
        """Search, enforce document scope, and translate PDF tile IDs."""

        candidate_count = request.top_k * len(self._documents_by_source)
        response = self._transport(
            f"{self._endpoint}/search",
            {
                "queries": [{"text": request.query}],
                "n_docs": candidate_count,
                "include_images": False,
            },
            self._timeout_seconds,
        )
        hits = _extract_single_query_hits(response)
        translated = tuple(self._translate_hit(hit) for hit in hits)
        return tuple(
            result
            for result in translated
            if request.source_scope.allows(result.document_id)
        )[: request.top_k]

    def _translate_hit(self, hit: object) -> VisualSearchResult:
        if not isinstance(hit, dict):
            raise PixelRagResponseError("PixelRAG hit must be a JSON object.")

        try:
            source = str(hit["url"])
            tile_index = int(hit["tile_index"])
            chunk_index = int(hit["chunk_index"])
            article_id = int(hit["article_id"])
            score = float(hit["score"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PixelRagResponseError(
                "PixelRAG hit is missing required page metadata."
            ) from exc
        if tile_index < 0 or chunk_index < 0 or article_id < 0:
            raise PixelRagResponseError(
                "PixelRAG hit contains a negative vendor identifier."
            )

        source_path = _resolve_vendor_source(
            source,
            self._vendor_working_directory,
        )
        document_id = self._documents_by_source.get(_path_key(source_path))
        if document_id is None:
            raise PixelRagResponseError(
                f"PixelRAG hit has no project document mapping: {source}"
            )

        # PixelRAG 0.4.0 renders each complete PDF page as one zero-based tile.
        page_number = tile_index + 1
        vector_id = hit.get("vector_id", "unknown")
        return VisualSearchResult(
            document_id=document_id,
            page_id=f"{document_id}:page:{page_number}",
            source_locator=PdfPageLocator(page_number),
            score=score,
            representation_ref=(
                f"pixelrag://article/{article_id}/tile/{tile_index}"
                f"/chunk/{chunk_index}"
            ),
            diagnostics=(f"vector_id={vector_id}",),
        )


def _extract_single_query_hits(response: object) -> list[object]:
    if not isinstance(response, dict):
        raise PixelRagResponseError("PixelRAG response must be a JSON object.")
    results = response.get("results")
    if not isinstance(results, list) or len(results) != 1:
        raise PixelRagResponseError(
            "PixelRAG response must contain exactly one query result."
        )
    query_result = results[0]
    if not isinstance(query_result, dict):
        raise PixelRagResponseError(
            "PixelRAG query result must be a JSON object."
        )
    hits = query_result.get("hits")
    if not isinstance(hits, list):
        raise PixelRagResponseError("PixelRAG query result has no hits list.")
    return hits


def _resolve_vendor_source(source: str, working_directory: Path) -> Path:
    parsed = urlparse(source)
    if parsed.scheme == "file":
        raw_path = unquote(parsed.path)
        if os.name == "nt" and len(raw_path) > 2 and raw_path[0] == "/":
            raw_path = raw_path[1:]
        selected_path = Path(raw_path)
    else:
        selected_path = Path(source)
    if not selected_path.is_absolute():
        selected_path = working_directory / selected_path
    return selected_path.resolve()


def _path_key(path: Path) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def _post_json(
    endpoint: str,
    payload: dict[str, object],
    timeout_seconds: float,
) -> object:
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PixelRagResponseError(
            f"PixelRAG search request failed: {endpoint}"
        ) from exc
