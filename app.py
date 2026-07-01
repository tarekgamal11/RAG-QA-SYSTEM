from __future__ import annotations
from pathlib import Path
import streamlit as st
from src.pipeline import EgyptTravelRAGPipeline
st.set_page_config(page_title="Egypt Travel Guide RAG", page_icon="🇪🇬", layout="wide")
st.title("Egypt Travel Guide RAG QA Assistant")
st.caption("Ask questions about tours, transfers, destinations, prices, and travel guide pages scraped from EgyptTravelGuide.com.")

@st.cache_resource(show_spinner=False)
def load_pipeline(index_dir: str, use_gemini_query: bool) -> EgyptTravelRAGPipeline:
    return EgyptTravelRAGPipeline(index_dir=index_dir, use_gemini_query_intelligence=use_gemini_query)


with st.sidebar:
    st.header("Settings")
    index_dir = st.text_input("Index directory", value="indexes")
    mode = st.selectbox("Retrieval mode", options=["hybrid", "dense", "sparse"], index=0)
    top_k = st.slider("Top-k chunks", min_value=1, max_value=10, value=5)
    use_gemini_query = st.checkbox("Use Gemini for query rewriting/classification", value=True)
    st.markdown("---")
    st.markdown("Run indexing first if the app cannot load indexes:")
    st.code(
        "python -m src.scraper --max-pages 120\n"
        "python -m src.cleaner\n"
        "python -m src.chunker\n"
        "python -m src.embed_index",
        language="bash",
    )

required_files = [Path(index_dir) / "faiss.index", Path(index_dir) / "bm25.pkl", Path(index_dir) / "metadata.pkl"]
missing = [str(p) for p in required_files if not p.exists()]
if missing:
    st.error("Index files are missing. Build the dataset and indexes first.")
    st.write("Missing files:", missing)
    st.stop()

question = st.text_input(
    "Your question",
    placeholder="Example: What snorkeling tours are available from Hurghada under 40 EUR?",
)
submit = st.button("Ask", type="primary")

if submit and question.strip():
    with st.spinner("Retrieving context and generating answer..."):
        pipeline = load_pipeline(index_dir, use_gemini_query)
        output = pipeline.run(question.strip(), mode=mode, top_k=top_k)

    st.subheader("Final Answer")
    st.write(output["answer"])

    qa = output["query_analysis"]
    st.subheader("Query Intelligence")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original query**")
        st.write(qa["original_query"])
        st.markdown("**Rewritten query**")
        st.write(qa["rewritten_query"])
    with col2:
        st.markdown("**Query class**")
        st.code(qa["query_class"])
        st.markdown("**Extracted filters**")
        st.json(qa["filters"])

    st.subheader("Retrieved Source Chunks")
    for result in output["results"]:
        chunk = result["chunk"]
        metadata = chunk["metadata"]
        title = metadata.get("title") or "Untitled"
        score = result.get("score")
        with st.expander(f"#{result['rank']} — {title} | score={score:.5f}"):
            st.markdown("**Metadata**")
            st.json(metadata)
            st.markdown("**Scores**")
            st.json(
                {
                    "final_score": result.get("score"),
                    "dense_score": result.get("dense_score"),
                    "bm25_score": result.get("bm25_score"),
                    "hybrid_score": result.get("hybrid_score"),
                }
            )
            st.markdown("**Chunk text**")
            st.write(chunk["text"])
