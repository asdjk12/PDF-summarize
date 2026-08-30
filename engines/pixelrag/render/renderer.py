"""使用 PixelRAG Render 将只读 PDF 转换为逐页视觉资产。"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

from pixelrag_render.render import render_pdf

from ..contracts import DocumentDescriptor, VisualAsset


class RenderError(RuntimeError):
    """表示 PDF 渲染或渲染产物校验失败。"""


class DocumentRenderer:
    """渲染单份 PDF，并返回顺序稳定、可追溯的视觉资产。"""

    def __init__(
        self,
        state_root: str | Path,
        *,
        dpi: int = 200,
        quality: int = 85,
    ) -> None:
        """配置模块自有的派生状态目录和 PixelRAG 渲染参数。"""

        self._state_root = Path(state_root).expanduser().resolve()
        self._dpi = dpi
        self._quality = quality

    def render(self, document: DocumentDescriptor) -> list[VisualAsset]:
        """将一份 PDF 渲染为每页一个 ``VisualAsset``。"""

        document_key = self._storage_key(document.document_id)
        version_key = self._storage_key(document.content_hash)
        document_root = self._state_root / "assets" / document_key
        final_dir = document_root / version_key
        staging_dir = document_root / f".{version_key}.{uuid4().hex}.staging"

        try:
            document_root.mkdir(parents=True, exist_ok=True)
            staging_dir.mkdir()
            rendered_dirs = render_pdf(
                document.source_path,
                staging_dir,
                dpi=self._dpi,
                quality=self._quality,
                stem="pages",
            )
            page_count = self._validate_render(rendered_dirs, staging_dir)
            self._replace_version(staging_dir, final_dir)
        except Exception as exc:
            if isinstance(exc, RenderError):
                raise
            raise RenderError(
                f"failed to render document {document.document_id!r}"
            ) from exc
        finally:
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)

        tile_dir = final_dir / "pages.png.tiles"
        return [
            VisualAsset(
                asset_id=(
                    f"{document.document_id}_page_{page_number:04d}"
                ),
                document_id=document.document_id,
                asset_type="pdf_page",
                sequence=page_number,
                visual_path=str(
                    (tile_dir / f"tile_{page_number - 1:04d}.jpg").resolve()
                ),
                source_location={"page": page_number},
            )
            for page_number in range(1, page_count + 1)
        ]

    @staticmethod
    def _storage_key(value: str) -> str:
        """将外部标识转换为固定、不可穿越目录的存储键。"""

        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_render(
        rendered_dirs: list[Path],
        staging_dir: Path,
    ) -> int:
        """验证 PixelRAG 页图清单、顺序和文件完整性。"""

        expected_tile_dir = staging_dir / "pages.png.tiles"
        if len(rendered_dirs) != 1:
            raise RenderError("PixelRAG returned an unexpected render layout")
        if Path(rendered_dirs[0]).resolve() != expected_tile_dir.resolve():
            raise RenderError("PixelRAG returned an unexpected tile directory")

        manifest_path = expected_tile_dir / "tiles.json"
        chunks_path = expected_tile_dir / "chunks.json"
        if not manifest_path.is_file() or not chunks_path.is_file():
            raise RenderError("PixelRAG render manifests are incomplete")

        with manifest_path.open(encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)

        tiles = manifest.get("tiles")
        total_pages = manifest.get("total_pages")
        if manifest.get("complete") is not True:
            raise RenderError("PixelRAG render is not marked complete")
        if type(total_pages) is not int or total_pages < 1:
            raise RenderError("PixelRAG render contains no PDF pages")
        if not isinstance(tiles, list) or total_pages != len(tiles):
            raise RenderError("PixelRAG tile count does not match total pages")

        expected_tiles = [
            f"tile_{index:04d}.jpg" for index in range(total_pages)
        ]
        if tiles != expected_tiles:
            raise RenderError("PixelRAG tile order or naming is invalid")
        if any(
            not (expected_tile_dir / tile_name).is_file()
            for tile_name in expected_tiles
        ):
            raise RenderError("PixelRAG render is missing one or more page images")

        return total_pages

    @staticmethod
    def _replace_version(staging_dir: Path, final_dir: Path) -> None:
        """校验完成后，用 staging 替换模块自有的同版本派生目录。"""

        if final_dir.exists():
            shutil.rmtree(final_dir)
        staging_dir.replace(final_dir)
