# Egypt Travel Guide RAG QA System

The project uses public pages from [Egypt Travel Guide](https://www.egypttravelguide.com/) as the knowledge base. The app can answer travel questions about tours, destinations, transfers, prices, and recommendations using retrieved website context and Gemini API generation.

## Features

- Responsible website scraping with `requests` and `BeautifulSoup`
- JSONL dataset creation
- Section-aware chunking with metadata
- Dense retrieval using Sentence Transformers + FAISS
- Sparse retrieval using BM25
- Hybrid retrieval using Reciprocal Rank Fusion
- Query rewriting, classification, and structured filter extraction
- Gemini API grounded answer generation
- Streamlit GUI showing:
  - final answer
  - original query
  - rewritten query
  - query class
  - extracted filters
  - retrieved chunks
  - scores
  - source metadata

## Project structure

```text
.
├── app.py
├── data/
│   ├── sample_clean_pages.jsonl
│   ├── raw_pages.jsonl
│   ├── clean_pages.jsonl
│   └── chunks.jsonl
├── evaluation/
│   └── dense_vs_hybrid.md
├── indexes/
│   ├── faiss.index
│   ├── bm25.pkl
│   └── metadata.pkl
├── src/
│   ├── scraper.py
│   ├── cleaner.py
│   ├── chunker.py
│   ├── embed_index.py
│   ├── query_intelligence.py
│   ├── retriever.py
│   ├── generator.py
│   ├── pipeline.py
│   └── evaluate_retrieval.py
├── requirements.txt
├── .env.example
└── report.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Create your `.env` file:

```bash
cp .env.example .env
```

Then add your real Gemini key:

```env
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Do not commit `.env` to GitHub.

## Full pipeline

### 1. Scrape website pages

```bash
python -m src.scraper --max-pages 120 --delay 1.0 --output data/raw_pages.jsonl
```

### 2. Clean pages

```bash
python -m src.cleaner --input data/raw_pages.jsonl --output data/clean_pages.jsonl
```

### 3. Create chunks

```bash
python -m src.chunker --input data/clean_pages.jsonl --output data/chunks.jsonl
```

### 4. Build indexes

```bash
python -m src.embed_index --chunks data/chunks.jsonl --output-dir indexes
```

### 5. Ask a question from CLI

```bash
python -m src.pipeline "What snorkeling tours are available from Hurghada under 40 EUR?" --mode hybrid --top-k 5
```

### 6. Run Streamlit GUI

```bash
streamlit run app.py
```

## Offline quick test using sample data

If you want to test the pipeline before scraping, use the included small sample dataset:

```bash
python -m src.chunker --input data/sample_clean_pages.jsonl --output data/chunks.jsonl
python -m src.embed_index --chunks data/chunks.jsonl --output-dir indexes
streamlit run app.py
```

The sample data is only for smoke testing. For the final project, use the scraped dataset.

## Example questions

```text
What snorkeling tours are available from Hurghada under 40 EUR?
Compare Sharm El Naga and Orange Bay.
Is Sindbad Submarine suitable for families?
What airport transfer options are available from Hurghada?
Recommend a Red Sea activity for children.
```

## Dense-only vs hybrid comparison

After building the indexes, run:

```bash
python -m src.evaluate_retrieval --output evaluation/dense_vs_hybrid.md
```

Then add your observations to the generated Markdown file.

## Notes on academic integrity

The core RAG code, retrieval logic, chunking, Gemini prompts, and hybrid search are written in this repository. AI help was used for project planning, code drafting, and documentation support. You should understand every file before submitting.
