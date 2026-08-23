"""
Splits long documents into overlapping chunks suitable for embedding.
Uses a simple, dependency-light character-based splitter with sentence
boundary awareness so chunks don't cut words/sentences mid-way when avoidable.
"""
import re

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_into_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return SENTENCE_SPLIT_RE.split(text)


def chunk_text(
    text: str, chunk_size: int = 800, chunk_overlap: int = 120
) -> list[str]:
    """
    Greedily packs sentences into chunks of ~chunk_size characters,
    carrying `chunk_overlap` characters of context into the next chunk.
    """
    sentences = _split_into_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            # start next chunk with overlap from the tail of the previous one
            overlap_text = current[-chunk_overlap:] if chunk_overlap else ""
            current = f"{overlap_text} {sentence}".strip()
        else:
            # single sentence longer than chunk_size: hard split
            for i in range(0, len(sentence), chunk_size):
                chunks.append(sentence[i : i + chunk_size])
            current = ""

    if current:
        chunks.append(current)

    return chunks
