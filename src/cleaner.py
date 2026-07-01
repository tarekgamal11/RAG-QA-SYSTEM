from __future__ import annotations
import argparse
import re
from typing import Any
from src.utils import clean_whitespace, read_jsonl, write_jsonl

NOISE_PATTERNS = [
    r"Home\s+Hurghada\s+Marsa Alam\s+Sharm el Sheikh\s+Transfer\s+Blog\s+Package Tour",
    r"You guided us to offer you the best",
    r"\* \* \*",
    r"READ MORE",
    r"DISCOVER TOURS",
]


def remove_noise(text: str) -> str:
    text = text or ""
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.I)
    text = re.sub(r"\b(Share|Facebook|Twitter|Instagram|Pinterest|YouTube)\b", " ", text, flags=re.I)
    return clean_whitespace(text)


def clean_sections(sections: dict[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for heading, body in sections.items():
        h = remove_noise(heading)[:100] or "main"
        b = remove_noise(body)
        if len(b) >= 30:
            cleaned[h] = b
    return cleaned


def clean_record(record: dict[str, Any]) -> dict[str, Any] | None:
    sections = clean_sections(record.get("sections", {}))
    full_text = clean_whitespace("\n\n".join(f"{h}\n{b}" for h, b in sections.items()))
    if len(full_text) < 100:
        return None

    title = remove_noise(record.get("title") or "Untitled")
    cleaned = {
        "url": record.get("url"),
        "title": title,
        "page_type": record.get("page_type", "general"),
        "price_eur": record.get("price_eur"),
        "locations": record.get("locations", []),
        "activities": record.get("activities", []),
        "sections": sections,
        "full_text": full_text,
        "text_length": len(full_text),
    }
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw_pages.jsonl")
    parser.add_argument("--output", default="data/clean_pages.jsonl")
    args = parser.parse_args()

    raw_records = read_jsonl(args.input)
    clean_records = []
    seen_urls: set[str] = set()
    for record in raw_records:
        url = record.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        cleaned = clean_record(record)
        if cleaned:
            clean_records.append(cleaned)

    write_jsonl(args.output, clean_records)
    print(f"Cleaned {len(clean_records)} pages -> {args.output}")


if __name__ == "__main__":
    main()
