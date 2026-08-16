from __future__ import annotations

from dataclasses import dataclass

from combine_format import BlockType, CanonicalDocument, ContentBlock


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    """Deterministic limits for downstream summary/retrieval chunks."""

    max_characters: int = 4_000

    def __post_init__(self) -> None:
        if self.max_characters <= 0:
            raise ValueError("max_characters must be greater than zero.")


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    ordinal: int
    document_id: str
    source_name: str
    text: str
    section_path: tuple[str, ...]
    page_numbers: tuple[int, ...]
    block_ids: tuple[str, ...]

    @property
    def character_count(self) -> int:
        return len(self.text)


def chunk_document(
    document: CanonicalDocument,
    config: ChunkingConfig | None = None,
) -> tuple[Chunk, ...]:
    """Create section-aware, source-traceable chunks from one document."""

    selected_config = config or ChunkingConfig()
    chunks: list[Chunk] = []
    current_blocks: list[tuple[ContentBlock, int, str]] = []
    current_section: tuple[str, ...] = ()
    current_length = 0

    def flush() -> None:
        nonlocal current_blocks, current_section, current_length
        if not current_blocks:
            return

        text = "\n\n".join(rendered for _, _, rendered in current_blocks)
        page_numbers = tuple(
            dict.fromkeys(page_number for _, page_number, _ in current_blocks)
        )
        ordinal = len(chunks)
        chunks.append(
            Chunk(
                chunk_id=f"{document.document_id}:chunk:{ordinal}",
                ordinal=ordinal,
                document_id=document.document_id,
                source_name=document.source.source_name,
                text=text,
                section_path=current_section,
                page_numbers=page_numbers,
                block_ids=tuple(
                    dict.fromkeys(
                        block.block_id for block, _, _ in current_blocks
                    )
                ),
            )
        )
        current_blocks = []
        current_section = ()
        current_length = 0

    for segment in document.segments:
        page_number = segment.locator.page_number

        for block in segment.blocks:
            rendered = _render_block(block)
            if not rendered:
                continue

            for fragment in _split_text(
                rendered,
                selected_config.max_characters,
            ):
                separator_length = 2 if current_blocks else 0
                would_exceed_limit = (
                    current_length + separator_length + len(fragment)
                    > selected_config.max_characters
                )
                section_changed = bool(current_blocks) and (
                    block.section_path != current_section
                )

                if section_changed or would_exceed_limit:
                    flush()

                if not current_blocks:
                    current_section = block.section_path

                current_blocks.append((block, page_number, fragment))
                current_length += (
                    (2 if len(current_blocks) > 1 else 0) + len(fragment)
                )

    flush()
    return tuple(chunks)


def _render_block(block: ContentBlock) -> str:
    if not block.text:
        return ""
    if block.type is BlockType.HEADING and block.heading_rank is not None:
        return f"{'#' * min(block.heading_rank, 6)} {block.text}"
    return block.text


def _split_text(text: str, limit: int) -> tuple[str, ...]:
    """Split an oversized block at whitespace when possible."""

    if len(text) <= limit:
        return (text,)

    fragments: list[str] = []
    remaining = text.strip()

    while len(remaining) > limit:
        split_at = remaining.rfind(" ", 0, limit + 1)
        if split_at <= 0:
            split_at = limit

        fragment = remaining[:split_at].rstrip()
        if fragment:
            fragments.append(fragment)
        remaining = remaining[split_at:].lstrip()

    if remaining:
        fragments.append(remaining)

    return tuple(fragments)
