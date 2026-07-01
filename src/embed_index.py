from __future__ import annotations
import argparse
import json
import pickle
from pathlib import Path
import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from src.utils import read_jsonl, tokenize

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def embed_texts(model: SentenceTransformer, texts: list[str], batch_size: int = 32) -> np.ndarray:
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.astype("float32")


def build_indexes(chunks_path: str, output_dir: str, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
    chunks = read_jsonl(chunks_path)
    if not chunks:
        raise ValueError(f"No chunks found in {chunks_path}. Run scraper, cleaner, and chunker first.")

    texts = [chunk["text"] for chunk in chunks]
    model = SentenceTransformer(model_name)
    embeddings = embed_texts(model, texts)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output / "faiss.index"))

    tokenized_corpus = [tokenize(text) for text in tqdm(texts, desc="Tokenizing for BM25")]
    bm25 = BM25Okapi(tokenized_corpus)

    with (output / "bm25.pkl").open("wb") as f:
        pickle.dump(bm25, f)

    payload = {
        "chunks": chunks,
        "embedding_model": model_name,
        "embedding_dimension": int(embeddings.shape[1]),
    }
    with (output / "metadata.pkl").open("wb") as f:
        pickle.dump(payload, f)

    with (output / "index_config.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "chunks_path": chunks_path,
                "embedding_model": model_name,
                "num_chunks": len(chunks),
                "embedding_dimension": int(embeddings.shape[1]),
            },
            f,
            indent=2,
        )

    print(f"Saved FAISS + BM25 indexes to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", default="data/chunks.jsonl")
    parser.add_argument("--output-dir", default="indexes")
    parser.add_argument("--model", default=DEFAULT_EMBEDDING_MODEL)
    args = parser.parse_args()
    build_indexes(args.chunks, args.output_dir, args.model)


if __name__ == "__main__":
    main()
