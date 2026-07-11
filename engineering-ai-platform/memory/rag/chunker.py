"""Chunker — divisão de documentos em chunks para indexação."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    content: str
    index: int
    source: str
    start_char: int
    end_char: int


class TextChunker:
    """Divide textos em chunks com overlap para RAG."""

    def __init__(self, chunk_size: int = 512, overlap: int = 64) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        if not text.strip():
            return []

        chunks: list[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + self._chunk_size, len(text))

            if end < len(text):
                break_point = text.rfind("\n", start, end)
                if break_point == -1 or break_point <= start:
                    break_point = text.rfind(" ", start, end)
                if break_point > start:
                    end = break_point + 1

            chunks.append(Chunk(
                content=text[start:end].strip(),
                index=index,
                source=source,
                start_char=start,
                end_char=end,
            ))

            if end >= len(text):
                break

            start = end - self._overlap
            index += 1

        return chunks

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def overlap(self) -> int:
        return self._overlap
