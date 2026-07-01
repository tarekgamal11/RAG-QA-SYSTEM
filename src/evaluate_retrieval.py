from __future__ import annotations

import argparse
from pathlib import Path

from src.query_intelligence import analyze_query
from src.retriever import TravelRetriever

DEFAULT_QUERIES = [
    "Is Sindbad Submarine suitable for claustrophobic people?",
    "Cheap snorkeling tours from Hurghada under 40 EUR",
    "Compare Sharm El Naga and Orange Bay",
]


def summarize_results(results: list[dict], max_chars: int = 220) -> str:
    lines = []
    for result in results:
        metadata = result["chunk"]["metadata"]
        text = result["chunk"]["text"].replace("\n", " ")[:max_chars]
        lines.append(
            f"{result['rank']}. **{metadata.get('title')}** — score `{result['score']:.5f}`  \n"
            f"   URL: {metadata.get('url')}  \n"
            f"   Section: {metadata.get('section')}  \n"
            f"   Snippet: {text}..."
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-dir", default="indexes")
    parser.add_argument("--output", default="evaluation/dense_vs_hybrid.md")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    retriever = TravelRetriever(index_dir=args.index_dir)
    sections = ["# Dense-only vs Hybrid Retrieval Comparison\n"]

    for query in DEFAULT_QUERIES:
        analysis = analyze_query(query, use_gemini=False)
        dense = retriever.search(analysis.rewritten_query, mode="dense", top_k=args.top_k, filters=analysis.filters)
        hybrid = retriever.search(analysis.rewritten_query, mode="hybrid", top_k=args.top_k, filters=analysis.filters)
        sections.append(f"## Query: {query}\n")
        sections.append(f"**Rewritten query:** {analysis.rewritten_query}  \n")
        sections.append(f"**Query class:** {analysis.query_class}  \n")
        sections.append(f"**Filters:** `{analysis.filters.model_dump()}`\n")
        sections.append("### Dense-only top results\n")
        sections.append(summarize_results(dense) or "No dense results.")
        sections.append("\n### Hybrid top results\n")
        sections.append(summarize_results(hybrid) or "No hybrid results.")
        sections.append(
            "\n### Analysis\n"
            "Fill this after running the system. State which retrieval mode performed better and why. "
            "Look for exact place names, warnings, prices, and whether the retrieved chunks directly answer the query.\n"
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sections), encoding="utf-8")
    print(f"Saved comparison report -> {output}")


if __name__ == "__main__":
    main()
