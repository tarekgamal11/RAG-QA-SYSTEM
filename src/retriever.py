from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Literal

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.query_intelligence import QueryFilters
from src.utils import tokenize

SearchMode = Literal["dense", "sparse", "hybrid"]


class TravelRetriever:
    def __init__(self, index_dir: str = "indexes") -> None:
        index_path = Path(index_dir) / "faiss.index"
        metadata_path = Path(index_dir) / "metadata.pkl"
        bm25_path = Path(index_dir) / "bm25.pkl"

        missing = [str(p) for p in [index_path, metadata_path, bm25_path] if not p.exists()]
        if missing:
            raise FileNotFoundError(
                "Missing index files: " + ", ".join(missing) +
                ". Run: python -m src.embed_index --chunks data/chunks.jsonl"
            )

        self.index = faiss.read_index(str(index_path))
        with metadata_path.open("rb") as f:
            payload = pickle.load(f)
        self.chunks: list[dict[str, Any]] = payload["chunks"]
        self.embedding_model_name = payload["embedding_model"]
        self.embedder = SentenceTransformer(self.embedding_model_name)
        with bm25_path.open("rb") as f:
            self.bm25 = pickle.load(f)

    def _embed_query(self, query: str) -> np.ndarray:
        embedding = self.embedder.encode([query], normalize_embeddings=True, convert_to_numpy=True)
        return embedding.astype("float32")

    @staticmethod
    def _passes_filters(chunk: dict[str, Any], filters: QueryFilters | dict[str, Any] | None) -> bool:
        if filters is None:
            return True
        if isinstance(filters, QueryFilters):
            f = filters.model_dump()
        else:
            f = filters
        metadata = chunk.get("metadata", {})

        location = f.get("location")
        if location:
            locs = [str(x).lower() for x in metadata.get("locations", [])]
            if location.lower() not in locs and location.lower() not in chunk.get("text", "").lower():
                return False

        activity = f.get("activity")
        if activity:
            acts = [str(x).lower() for x in metadata.get("activities", [])]
            if activity.lower() not in acts and activity.lower().replace("_", " ") not in chunk.get("text", "").lower():
                return False

        page_type = f.get("page_type")
        if page_type and metadata.get("page_type") != page_type:
            return False

        price = metadata.get("price_eur")
        min_price = f.get("min_price_eur")
        max_price = f.get("max_price_eur")
        if min_price is not None or max_price is not None:
            if price is None:
                return False
            try:
                price_float = float(price)
            except (TypeError, ValueError):
                return False
            if min_price is not None and price_float < float(min_price):
                return False
            if max_price is not None and price_float > float(max_price):
                return False

        return True

    def dense_search(self, query: str, top_k: int = 5, filters: QueryFilters | None = None, fetch_k: int = 60) -> list[dict[str, Any]]:
        q_emb = self._embed_query(query)
        scores, indices = self.index.search(q_emb, min(fetch_k, len(self.chunks)))
        results: list[dict[str, Any]] = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < 0:
                continue
            chunk = self.chunks[int(idx)]
            if not self._passes_filters(chunk, filters):
                continue
            results.append(
                {
                    "index": int(idx),
                    "rank": rank + 1,
                    "score": float(score),
                    "dense_score": float(score),
                    "bm25_score": None,
                    "hybrid_score": None,
                    "chunk": chunk,
                }
            )
            if len(results) >= top_k:
                break
        return results

    def sparse_search(self, query: str, top_k: int = 5, filters: QueryFilters | None = None, fetch_k: int = 60) -> list[dict[str, Any]]:
        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        ranked = np.argsort(scores)[::-1][: min(fetch_k, len(scores))]
        results: list[dict[str, Any]] = []
        for rank, idx in enumerate(ranked):
            chunk = self.chunks[int(idx)]
            if not self._passes_filters(chunk, filters):
                continue
            results.append(
                {
                    "index": int(idx),
                    "rank": rank + 1,
                    "score": float(scores[idx]),
                    "dense_score": None,
                    "bm25_score": float(scores[idx]),
                    "hybrid_score": None,
                    "chunk": chunk,
                }
            )
            if len(results) >= top_k:
                break
        return results

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        filters: QueryFilters | None = None,
        fetch_k: int = 80,
        dense_weight: float = 0.55,
        sparse_weight: float = 0.45,
        rrf_k: int = 60,
    ) -> list[dict[str, Any]]:
        dense = self.dense_search(query, top_k=fetch_k, filters=filters, fetch_k=fetch_k)
        sparse = self.sparse_search(query, top_k=fetch_k, filters=filters, fetch_k=fetch_k)

        fused: dict[int, dict[str, Any]] = {}
        for rank, result in enumerate(dense, start=1):
            idx = result["index"]
            fused.setdefault(idx, {"chunk": result["chunk"], "dense_score": None, "bm25_score": None, "hybrid_score": 0.0})
            fused[idx]["dense_score"] = result["dense_score"]
            fused[idx]["hybrid_score"] += dense_weight * (1.0 / (rrf_k + rank))

        for rank, result in enumerate(sparse, start=1):
            idx = result["index"]
            fused.setdefault(idx, {"chunk": result["chunk"], "dense_score": None, "bm25_score": None, "hybrid_score": 0.0})
            fused[idx]["bm25_score"] = result["bm25_score"]
            fused[idx]["hybrid_score"] += sparse_weight * (1.0 / (rrf_k + rank))

        sorted_items = sorted(fused.items(), key=lambda item: item[1]["hybrid_score"], reverse=True)
        results: list[dict[str, Any]] = []
        for rank, (idx, item) in enumerate(sorted_items[:top_k], start=1):
            results.append(
                {
                    "index": idx,
                    "rank": rank,
                    "score": float(item["hybrid_score"]),
                    "dense_score": item["dense_score"],
                    "bm25_score": item["bm25_score"],
                    "hybrid_score": float(item["hybrid_score"]),
                    "chunk": item["chunk"],
                }
            )
        return results

    def search(self, query: str, mode: SearchMode = "hybrid", top_k: int = 5, filters: QueryFilters | None = None) -> list[dict[str, Any]]:
        if mode == "dense":
            return self.dense_search(query, top_k=top_k, filters=filters)
        if mode == "sparse":
            return self.sparse_search(query, top_k=top_k, filters=filters)
        return self.hybrid_search(query, top_k=top_k, filters=filters)
