"""编排 PixelRAG 的单文档索引、证据检索与派生状态删除。"""

from __future__ import annotations

from pathlib import Path

from ..adapter import DocumentAdapter
from ..contracts import DocumentDescriptor, RetrievedAsset, VisualAsset
from ..embed import PixelRAGVisualEmbedder
from ..index import PixelRAGFaissIndex
from ..manifest import AssetManifest, AssetNotFoundError
from ..render import DocumentRenderer


class RetrievalError(RuntimeError):
    """表示检索请求或 provenance 解析失败。"""


class DocumentRetrievalEngine:
    """隐藏 PixelRAG 内部细节，只公开 index、search 和 delete。"""

    def __init__(
        self,
        state_root: str | Path,
        model_path: str | Path,
        *,
        device: str = "cuda",
    ) -> None:
        """组装 PDF v1 的五个内部 seam，并加载一次本地模型。"""

        self._adapter = DocumentAdapter()
        self._renderer = DocumentRenderer(state_root)
        self._manifest = AssetManifest()
        self._embedder = PixelRAGVisualEmbedder(model_path, device=device)
        self._vector_index = PixelRAGFaissIndex()

    def index(self, document: DocumentDescriptor) -> None:
        """索引一个上游文档，并以内容版本为单位完成替换。"""

        prepared = self._adapter.prepare(document)
        previous_hash = self._manifest.get_content_hash(prepared.document_id)
        if previous_hash == prepared.content_hash:
            return

        previous_assets = self._manifest.get_by_document(prepared.document_id)
        assets = self._renderer.render(prepared)
        try:
            embeddings = self._embedder.embed_assets(assets)
            self._manifest.register(prepared, assets)
            try:
                self._vector_index.upsert(prepared.document_id, embeddings)
            except Exception:
                self._restore_manifest(prepared, previous_hash, previous_assets)
                raise
        except Exception:
            self._renderer.delete_version(
                prepared.document_id,
                prepared.content_hash,
            )
            raise

        if previous_hash is not None:
            self._renderer.delete_version(prepared.document_id, previous_hash)

    def search(
        self,
        query: str,
        filters: dict | None = None,
        top_k: int = 10,
    ) -> list[RetrievedAsset]:
        """检索并通过 Manifest 解析完整的证据候选。"""

        if not isinstance(query, str) or not query.strip():
            raise RetrievalError("query must be a non-empty string")
        if type(top_k) is not int or top_k < 1:
            raise RetrievalError("top_k must be a positive integer")

        query_vector = self._embedder.embed_query(query)
        matches = self._vector_index.search(query_vector, top_k, filters)
        results: list[RetrievedAsset] = []
        try:
            for asset_id, score in matches:
                asset = self._manifest.get(asset_id)
                results.append(
                    RetrievedAsset(
                        asset_id=asset.asset_id,
                        document_id=asset.document_id,
                        asset_type=asset.asset_type,
                        sequence=asset.sequence,
                        visual_path=asset.visual_path,
                        source_location=dict(asset.source_location),
                        score=score,
                        metadata={},
                    )
                )
        except AssetNotFoundError as exc:
            raise RetrievalError(
                "vector index result is missing from the asset manifest"
            ) from exc
        return results

    def delete(self, document_id: str) -> None:
        """幂等删除文档的全部 PixelRAG 派生状态。"""

        if not isinstance(document_id, str) or not document_id:
            raise RetrievalError("document_id must be a non-empty string")
        self._vector_index.delete_document(document_id)
        self._manifest.remove_document(document_id)
        self._renderer.delete_document(document_id)

    def _restore_manifest(
        self,
        document: DocumentDescriptor,
        previous_hash: str | None,
        previous_assets: list[VisualAsset],
    ) -> None:
        """向量替换失败时恢复先前的 provenance 状态。"""

        if previous_hash is None:
            self._manifest.remove_document(document.document_id)
            return
        previous_document = DocumentDescriptor(
            document_id=document.document_id,
            source_path=document.source_path,
            content_hash=previous_hash,
            mime_type=document.mime_type,
        )
        self._manifest.register(previous_document, previous_assets)
