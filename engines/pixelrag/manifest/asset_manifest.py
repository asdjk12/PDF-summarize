"""在内存中维护文档与视觉资产之间的 provenance 映射。"""

from __future__ import annotations

from copy import deepcopy

from ..contracts import DocumentDescriptor, VisualAsset


class AssetNotFoundError(KeyError):
    """表示指定的资产 ID 不存在。"""


class AssetManifest:
    """保存资产真相，并以整文档粒度完成注册和替换。"""

    def __init__(self) -> None:
        """初始化进程内资产、文档页序和内容版本映射。"""

        self._assets_by_id: dict[str, VisualAsset] = {}
        self._asset_ids_by_document: dict[str, tuple[str, ...]] = {}
        self._content_hashes: dict[str, str] = {}

    def register(
        self,
        document: DocumentDescriptor,
        assets: list[VisualAsset],
    ) -> None:
        """验证全部资产后，原子替换指定文档的清单记录。"""

        ordered_assets = self._validated_assets(document, assets)
        stored_assets = tuple(deepcopy(asset) for asset in ordered_assets)

        next_assets = self._assets_by_id.copy()
        for asset_id in self._asset_ids_by_document.get(
            document.document_id,
            (),
        ):
            next_assets.pop(asset_id, None)
        for asset in stored_assets:
            next_assets[asset.asset_id] = asset

        next_document_assets = self._asset_ids_by_document.copy()
        next_document_assets[document.document_id] = tuple(
            asset.asset_id for asset in stored_assets
        )
        next_content_hashes = self._content_hashes.copy()
        next_content_hashes[document.document_id] = document.content_hash

        self._assets_by_id = next_assets
        self._asset_ids_by_document = next_document_assets
        self._content_hashes = next_content_hashes

    def get(self, asset_id: str) -> VisualAsset:
        """按资产 ID 返回与内部状态隔离的资产副本。"""

        try:
            asset = self._assets_by_id[asset_id]
        except KeyError as exc:
            raise AssetNotFoundError(asset_id) from exc
        return deepcopy(asset)

    def get_by_document(self, document_id: str) -> list[VisualAsset]:
        """按稳定页序返回指定文档的全部资产副本。"""

        asset_ids = self._asset_ids_by_document.get(document_id, ())
        return [deepcopy(self._assets_by_id[asset_id]) for asset_id in asset_ids]

    def get_content_hash(self, document_id: str) -> str | None:
        """返回文档当前登记的内容版本，未登记时返回 ``None``。"""

        return self._content_hashes.get(document_id)

    def remove_document(self, document_id: str) -> None:
        """幂等移除指定文档的清单和内容版本。"""

        asset_ids = self._asset_ids_by_document.pop(document_id, ())
        for asset_id in asset_ids:
            self._assets_by_id.pop(asset_id, None)
        self._content_hashes.pop(document_id, None)

    def _validated_assets(
        self,
        document: DocumentDescriptor,
        assets: list[VisualAsset],
    ) -> list[VisualAsset]:
        """在修改内部状态前验证文档归属、资产类型和 ID 唯一性。"""

        if not isinstance(document, DocumentDescriptor):
            raise TypeError("document must be a DocumentDescriptor")
        if not isinstance(assets, list):
            raise TypeError("assets must be a list")
        if not assets:
            raise ValueError("assets must not be empty")

        asset_ids: set[str] = set()
        for asset in assets:
            if not isinstance(asset, VisualAsset):
                raise TypeError("assets must contain only VisualAsset values")
            if asset.document_id != document.document_id:
                raise ValueError("asset document_id does not match document")
            if not isinstance(asset.asset_id, str) or not asset.asset_id:
                raise ValueError("asset_id must be a non-empty string")
            if asset.asset_id in asset_ids:
                raise ValueError(f"duplicate asset_id: {asset.asset_id!r}")

            existing = self._assets_by_id.get(asset.asset_id)
            if existing is not None and existing.document_id != document.document_id:
                raise ValueError(
                    f"asset_id already belongs to another document: "
                    f"{asset.asset_id!r}"
                )
            asset_ids.add(asset.asset_id)

        return sorted(assets, key=lambda asset: (asset.sequence, asset.asset_id))
