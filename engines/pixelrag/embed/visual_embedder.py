"""封装 PixelRAG 0.4.0 的 Qwen3-VL 页面与查询编码语义。"""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image
from pixelrag_embed.embed import (
    _clamp_width_pil as clamp_pixelrag_image,
    _init_direct_gpu as initialize_pixelrag_model,
)

from ..contracts import AssetEmbedding, VisualAsset


class EmbeddingError(RuntimeError):
    """表示模型加载、页面读取或向量编码失败。"""


class PixelRAGVisualEmbedder:
    """加载并复用本地 Qwen3-VL 模型生成归一化向量。"""

    PAGE_INSTRUCTION = "Represent the user's input."
    QUERY_INSTRUCTION = "Retrieve images or text relevant to the user's query."
    _BATCH_SIZE = 4

    def __init__(
        self,
        model_path: str | Path,
        *,
        device: str = "cuda",
    ) -> None:
        """在 CUDA 上以 BF16 加载一次 PixelRAG direct-GPU 模型。"""

        if device != "cuda":
            raise EmbeddingError("PixelRAG v1 embedding requires device='cuda'")
        if not torch.cuda.is_available():
            raise EmbeddingError("CUDA is not available for PixelRAG embedding")

        try:
            resolved_model_path = Path(model_path).expanduser().resolve(strict=True)
            if not resolved_model_path.is_dir():
                raise ValueError("model_path must be a directory")
            self._model, self._processor = initialize_pixelrag_model(
                str(resolved_model_path),
                gpu_id=0,
            )
        except Exception as exc:
            if isinstance(exc, EmbeddingError):
                raise
            raise EmbeddingError("failed to load PixelRAG embedding model") from exc

        self._device = device

    def embed_assets(self, assets: list[VisualAsset]) -> list[AssetEmbedding]:
        """按输入顺序编码页面图像，并逐项保留原始资产 ID。"""

        if not isinstance(assets, list):
            raise EmbeddingError("assets must be a list")
        if not assets:
            return []
        if any(not isinstance(asset, VisualAsset) for asset in assets):
            raise EmbeddingError("assets must contain only VisualAsset values")

        embeddings: list[AssetEmbedding] = []
        try:
            for offset in range(0, len(assets), self._BATCH_SIZE):
                batch = assets[offset : offset + self._BATCH_SIZE]
                images = [self._load_image(asset.visual_path) for asset in batch]
                conversations = [
                    [
                        {
                            "role": "system",
                            "content": [
                                {"type": "text", "text": self.PAGE_INSTRUCTION}
                            ],
                        },
                        {
                            "role": "user",
                            "content": [{"type": "image", "image": image}],
                        },
                    ]
                    for image in images
                ]
                vectors = self._encode(conversations, images)
                embeddings.extend(
                    AssetEmbedding(asset_id=asset.asset_id, vector=vector)
                    for asset, vector in zip(batch, vectors, strict=True)
                )
        except Exception as exc:
            if isinstance(exc, EmbeddingError):
                raise
            raise EmbeddingError("failed to embed visual assets") from exc

        return embeddings

    def embed_query(self, query: str) -> list[float]:
        """用检索 instruction 编码一条非空文本查询。"""

        if not isinstance(query, str) or not query.strip():
            raise EmbeddingError("query must be a non-empty string")

        conversation = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": self.QUERY_INSTRUCTION}
                ],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": query}],
            },
        ]
        try:
            return self._encode([conversation], images=None)[0]
        except Exception as exc:
            if isinstance(exc, EmbeddingError):
                raise
            raise EmbeddingError("failed to embed query") from exc

    @staticmethod
    def _load_image(visual_path: str) -> Image.Image:
        """读取 RGB 页面图，并复用 PixelRAG 的宽图对齐缩放。"""

        image_path = Path(visual_path).expanduser().resolve(strict=True)
        if not image_path.is_file():
            raise ValueError(f"visual asset is not a file: {image_path}")
        with Image.open(image_path) as source_image:
            image = source_image.convert("RGB")
        return clamp_pixelrag_image(image)

    def _encode(
        self,
        conversations: list[list[dict[str, object]]],
        images: list[Image.Image] | None,
    ) -> list[list[float]]:
        """执行 chat-template、last-token pooling 和 L2 normalization。"""

        texts = [
            self._processor.apply_chat_template(
                conversation,
                tokenize=False,
                add_generation_prompt=True,
            )
            for conversation in conversations
        ]
        processor_kwargs: dict[str, object] = {
            "text": texts,
            "return_tensors": "pt",
            "padding": True,
        }
        if images is not None:
            processor_kwargs["images"] = images
            processor_kwargs["device"] = self._device

        inputs = self._processor(**processor_kwargs)
        inputs = {
            name: value.to(self._device) if hasattr(value, "to") else value
            for name, value in inputs.items()
        }

        with torch.inference_mode():
            outputs = self._model.model(**inputs)

        last_hidden = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"]
        last_token_indices = attention_mask.sum(dim=1) - 1
        pooled = last_hidden[
            torch.arange(last_hidden.size(0), device=last_hidden.device),
            last_token_indices,
        ]
        normalized = torch.nn.functional.normalize(
            pooled.to(dtype=torch.float32),
            p=2,
            dim=-1,
        )
        return normalized.to(device="cpu").tolist()
