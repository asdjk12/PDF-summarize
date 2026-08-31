"""使用 FAISS IndexFlatIP 保存并检索视觉资产向量。"""

from __future__ import annotations

from dataclasses import dataclass

import faiss
import numpy as np

from ..contracts import AssetEmbedding


class VectorIndexError(RuntimeError):
    """表示向量、过滤条件或 FAISS 操作无效。"""


@dataclass(frozen=True, slots=True)
class _VectorRecord:
    """保存索引重建所需的最小内部记录。"""

    document_id: str
    vector: np.ndarray


class PixelRAGFaissIndex:
    """维护可按文档整体替换的进程内内积索引。"""

    def __init__(self) -> None:
        """初始化尚未确定维度的空索引。"""

        self._dimension: int | None = None
        self._index: faiss.IndexFlatIP | None = None
        self._records: dict[str, _VectorRecord] = {}
        self._row_asset_ids: list[str] = []
        self._row_by_asset_id: dict[str, int] = {}

    def upsert(
        self,
        document_id: str,
        embeddings: list[AssetEmbedding],
    ) -> None:
        """验证新向量后，整体替换指定文档的全部索引行。"""

        if not isinstance(document_id, str) or not document_id:
            raise VectorIndexError("document_id must be a non-empty string")
        if not isinstance(embeddings, list):
            raise VectorIndexError("embeddings must be a list")
        if not embeddings:
            raise VectorIndexError("embeddings must not be empty")

        try:
            vectors, dimension = self._validated_embeddings(
                document_id,
                embeddings,
            )
            next_records = {
                asset_id: record
                for asset_id, record in self._records.items()
                if record.document_id != document_id
            }
            next_records.update(
                {
                    asset_id: _VectorRecord(document_id, vector)
                    for asset_id, vector in vectors.items()
                }
            )
            self._replace_records(next_records, dimension)
        except Exception as exc:
            if isinstance(exc, VectorIndexError):
                raise
            raise VectorIndexError("failed to upsert document vectors") from exc

    def delete_document(self, document_id: str) -> None:
        """幂等删除指定文档的向量，并重建小型内存索引。"""

        if not isinstance(document_id, str) or not document_id:
            raise VectorIndexError("document_id must be a non-empty string")
        if not any(
            record.document_id == document_id
            for record in self._records.values()
        ):
            return

        next_records = {
            asset_id: record
            for asset_id, record in self._records.items()
            if record.document_id != document_id
        }
        try:
            self._replace_records(next_records, self._dimension)
        except Exception as exc:
            raise VectorIndexError("failed to delete document vectors") from exc

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[tuple[str, float]]:
        """以内积搜索资产 ID，并在过滤后按稳定分数顺序返回。"""

        if type(top_k) is not int or top_k < 1:
            raise VectorIndexError("top_k must be a positive integer")
        allowed_documents = self._validated_filters(filters)
        query = self._to_vector(
            query_vector,
            expected_dimension=self._dimension,
            label="query_vector",
        )
        if self._index is None or self._index.ntotal == 0:
            return []
        if allowed_documents is not None and not allowed_documents:
            return []

        try:
            scores, rows = self._index.search(
                np.ascontiguousarray(query.reshape(1, -1)),
                self._index.ntotal,
            )
        except Exception as exc:
            raise VectorIndexError("FAISS search failed") from exc

        matches = []
        for score, row in zip(scores[0], rows[0], strict=True):
            asset_id = self._row_asset_ids[int(row)]
            document_id = self._records[asset_id].document_id
            if allowed_documents is None or document_id in allowed_documents:
                matches.append((asset_id, float(score)))

        matches.sort(key=lambda match: (-match[1], match[0]))
        return matches[:top_k]

    def _validated_embeddings(
        self,
        document_id: str,
        embeddings: list[AssetEmbedding],
    ) -> tuple[dict[str, np.ndarray], int]:
        """在变更索引前验证身份唯一性、维度和数值有效性。"""

        dimension = self._dimension
        vectors: dict[str, np.ndarray] = {}
        for embedding in embeddings:
            if not isinstance(embedding, AssetEmbedding):
                raise VectorIndexError(
                    "embeddings must contain only AssetEmbedding values"
                )
            if not isinstance(embedding.asset_id, str) or not embedding.asset_id:
                raise VectorIndexError("asset_id must be a non-empty string")
            if embedding.asset_id in vectors:
                raise VectorIndexError(
                    f"duplicate asset_id: {embedding.asset_id!r}"
                )

            existing = self._records.get(embedding.asset_id)
            if existing is not None and existing.document_id != document_id:
                raise VectorIndexError(
                    f"asset_id already belongs to another document: "
                    f"{embedding.asset_id!r}"
                )

            vector = self._to_vector(
                embedding.vector,
                expected_dimension=dimension,
                label=f"embedding {embedding.asset_id!r}",
            )
            if dimension is None:
                dimension = int(vector.size)
            vectors[embedding.asset_id] = vector.copy()

        if dimension is None:
            raise VectorIndexError("embedding dimension could not be determined")
        return vectors, dimension

    @staticmethod
    def _to_vector(
        values: list[float],
        *,
        expected_dimension: int | None,
        label: str,
    ) -> np.ndarray:
        """转换为连续 float32 向量并拒绝非法数值。"""

        try:
            vector = np.asarray(values, dtype=np.float32)
        except (TypeError, ValueError) as exc:
            raise VectorIndexError(f"{label} must contain numeric values") from exc
        if vector.ndim != 1 or vector.size == 0:
            raise VectorIndexError(f"{label} must be a non-empty 1D vector")
        if expected_dimension is not None and vector.size != expected_dimension:
            raise VectorIndexError(
                f"{label} dimension {vector.size} does not match "
                f"index dimension {expected_dimension}"
            )
        if not np.isfinite(vector).all():
            raise VectorIndexError(f"{label} contains non-finite values")
        if float(np.linalg.norm(vector)) == 0.0:
            raise VectorIndexError(f"{label} must not be a zero vector")
        return np.ascontiguousarray(vector)

    @staticmethod
    def _validated_filters(filters: dict | None) -> set[str] | None:
        """仅接受 v1 的 document_ids 检索范围过滤。"""

        if filters is None:
            return None
        if not isinstance(filters, dict):
            raise VectorIndexError("filters must be a dictionary or None")
        unknown_keys = set(filters) - {"document_ids"}
        if unknown_keys:
            names = ", ".join(sorted(map(str, unknown_keys)))
            raise VectorIndexError(f"unsupported filter keys: {names}")
        if "document_ids" not in filters:
            return None

        document_ids = filters["document_ids"]
        if not isinstance(document_ids, list) or any(
            not isinstance(document_id, str) or not document_id
            for document_id in document_ids
        ):
            raise VectorIndexError(
                "filters['document_ids'] must be a list of non-empty strings"
            )
        return set(document_ids)

    def _replace_records(
        self,
        records: dict[str, _VectorRecord],
        dimension: int | None,
    ) -> None:
        """先重建 FAISS 行映射，成功后再整体提交内部状态。"""

        if dimension is None:
            index = None
            row_asset_ids: list[str] = []
        else:
            index = faiss.IndexFlatIP(dimension)
            row_asset_ids = sorted(records)
            if row_asset_ids:
                matrix = np.ascontiguousarray(
                    np.stack(
                        [records[asset_id].vector for asset_id in row_asset_ids]
                    ),
                    dtype=np.float32,
                )
                index.add(matrix)

        row_by_asset_id = {
            asset_id: row for row, asset_id in enumerate(row_asset_ids)
        }
        self._dimension = dimension
        self._records = records
        self._index = index
        self._row_asset_ids = row_asset_ids
        self._row_by_asset_id = row_by_asset_id
