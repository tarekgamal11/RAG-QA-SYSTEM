from __future__ import annotations
import argparse
from typing import Any
from src.utils import clean_whitespace, read_jsonl, slugify, write_jsonl


def split_text_with_overlap(text: str, max_chars: int = 1200, overlap_chars: int = 150) -> list[str]:
    text = clean_whitespace(text)
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            sentence_end = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if sentence_end > start + max_chars * 0.5:
                end = sentence_end + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap_chars)
    return chunks


def create_chunks(records: list[dict[str, Any]], max_chars: int, overlap_chars: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for page_i, record in enumerate(records):
        sections = record.get("sections") or {"main": record.get("full_text", "")}
        for section_title, section_text in sections.items():
            section_text = clean_whitespace(section_text)
            if len(section_text) < 40:
                continue
            section_chunks = split_text_with_overlap(section_text, max_chars=max_chars, overlap_chars=overlap_chars)
            for part_i, chunk_text in enumerate(section_chunks):
                chunk_id = f"p{page_i:04d}_{slugify(record.get('title', 'page'))}_{slugify(section_title)}_{part_i}"
                full_chunk_text = clean_whitespace(
                    f"Title: {record.get('title', 'Untitled')}\n"
                    f"Page type: {record.get('page_type', 'general')}\n"
                    f"Section: {section_title}\n"
                    f"Price EUR: {record.get('price_eur')}\n"
                    f"Locations: {', '.join(record.get('locations', []))}\n"
                    f"Activities: {', '.join(record.get('activities', []))}\n\n"
                    f"{chunk_text}"
                )
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "text": full_chunk_text,
                        "metadata": {
                            "url": record.get("url"),
                            "title": record.get("title"),
                            "page_type": record.get("page_type"),
                            "section": section_title,
                            "price_eur": record.get("price_eur"),
                            "locations": record.get("locations", []),
                            "activities": record.get("activities", []),
                            "source_page_index": page_i,
                        },
                    }
                )
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/clean_pages.jsonl")
    parser.add_argument("--output", default="data/chunks.jsonl")
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--overlap-chars", type=int, default=150)
    args = parser.parse_args()

    records = read_jsonl(args.input)
    chunks = create_chunks(records, max_chars=args.max_chars, overlap_chars=args.overlap_chars)
    write_jsonl(args.output, chunks)
    print(f"Created {len(chunks)} chunks -> {args.output}")


if __name__ == "__main__":
    main()
