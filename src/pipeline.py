from __future__ import annotations

import argparse
from typing import Any

from src.generator import generate_answer
from src.query_intelligence import QueryAnalysis, analyze_query
from src.retriever import SearchMode, TravelRetriever


class EgyptTravelRAGPipeline:
    def __init__(self, index_dir: str = "indexes", use_gemini_query_intelligence: bool = True) -> None:
        self.retriever = TravelRetriever(index_dir=index_dir)
        self.use_gemini_query_intelligence = use_gemini_query_intelligence

    def run(self, question: str, mode: SearchMode = "hybrid", top_k: int = 5) -> dict[str, Any]:
        query_info: QueryAnalysis = analyze_query(question, use_gemini=self.use_gemini_query_intelligence)
        results = self.retriever.search(
            query=query_info.rewritten_query,
            mode=mode,
            top_k=top_k,
            filters=query_info.filters,
        )
        answer = generate_answer(question, results)
        return {
            "answer": answer,
            "query_analysis": query_info.model_dump(),
            "retrieval_mode": mode,
            "results": results,
        }


def print_result(output: dict[str, Any]) -> None:
    qa = output["query_analysis"]
    print("\n=== QUERY INTELLIGENCE ===")
    print(f"Original query : {qa['original_query']}")
    print(f"Rewritten query: {qa['rewritten_query']}")
    print(f"Query class    : {qa['query_class']}")
    print(f"Filters        : {qa['filters']}")

    print("\n=== FINAL ANSWER ===")
    print(output["answer"])

    print("\n=== RETRIEVED CHUNKS ===")
    for result in output["results"]:
        chunk = result["chunk"]
        metadata = chunk["metadata"]
        print("-" * 80)
        print(f"Rank: {result['rank']} | Score: {result['score']:.5f}")
        print(f"Dense score: {result.get('dense_score')} | BM25 score: {result.get('bm25_score')}")
        print(f"Title: {metadata.get('title')}")
        print(f"URL: {metadata.get('url')}")
        print(f"Section: {metadata.get('section')}")
        print(chunk["text"][:700].replace("\n", " ") + "...")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", default="What snorkeling trips are available from Hurghada under 40 EUR?")
    parser.add_argument("--index-dir", default="indexes")
    parser.add_argument("--mode", choices=["dense", "sparse", "hybrid"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-gemini-query", action="store_true", help="Use local query intelligence instead of Gemini.")
    args = parser.parse_args()

    pipeline = EgyptTravelRAGPipeline(index_dir=args.index_dir, use_gemini_query_intelligence=not args.no_gemini_query)
    output = pipeline.run(args.question, mode=args.mode, top_k=args.top_k)
    print_result(output)


if __name__ == "__main__":
    main()
