from pathlib import Path
import shutil

import pandas as pd
import streamlit as st

from evaluation.test_queries import OFFICIAL_EVALUATION_QUERIES
from llm.generator import generate_answer
from retriever.corpus_loader import load_corpus
from retriever.chroma_retriever import chroma_index_exists
from retriever.retriever import EvidenceChunk, RetrievalRequest, retrieve_context
from retriever.semantic_retriever import semantic_index_exists
from ingestion.batch_ingestion import ingest_files_incrementally
from ingestion.pipeline import append_jsonl


st.set_page_config(
    page_title="Placement Intelligence Assistant",
    layout="wide",
)


DATA_DIR = Path("data")
CORPUS_PATH = DATA_DIR / "extracted" / "corpus.jsonl"


SAMPLE_QUERIES = [
    "Is the Amazon CGPA cutoff 6.4 or 7.0? Explain.",
    "Which company hires the most Interns?",
    "Which Python-focused company hires the most Interns?",
    "Which company's package grew the most from 2021 to 2024?",
    "I have CGPA 5.0. Where can I apply?",
]


def main() -> None:
    corpus = load_corpus(CORPUS_PATH)

    st.title("Placement Intelligence Assistant")
    st.caption("Grounded placement answers across eligibility tables, interview text, hiring charts, trends, and conflicts.")

    with st.sidebar:
        st.header("System status")
        st.metric("Corpus records", len(corpus))
        st.metric("Chroma index", "Ready" if chroma_index_exists() else "Not built")
        st.metric("Semantic index", "Ready" if semantic_index_exists() else "Not built")

        if corpus:
            sections = sorted({str(chunk.metadata.get("section", "unknown")) for chunk in corpus})
            st.caption("Indexed sections")
            st.write(", ".join(sections))

        st.header("Document upload")
        uploaded_files = st.file_uploader(
            "Upload PDFs, images, CSV, or Excel files",
            type=["pdf", "png", "jpg", "jpeg", "webp", "csv", "xlsx", "xls"],
            accept_multiple_files=True,
        )
        if uploaded_files and st.button("Ingest uploaded files", use_container_width=True):
            with st.spinner("Processing uploaded files..."):
                saved_paths = save_uploaded_files(uploaded_files)
                documents, skipped = ingest_files_incrementally(saved_paths)
                append_jsonl(documents, CORPUS_PATH)
            st.success(f"Ingested {len(documents)} records. Skipped {len(skipped)} duplicate file(s).")

        st.header("Retrieval controls")
        companies = sorted(
            {
                str(chunk.metadata["company"])
                for chunk in corpus
                if chunk.metadata.get("company")
            }
        )
        company_options = [""] + companies
        company = st.selectbox("Company filter", company_options)
        section_options = [""] + sorted(
            {
                str(chunk.metadata["section"])
                for chunk in corpus
                if chunk.metadata.get("section")
            }
        )
        section = st.selectbox("Section filter", section_options)
        top_k = st.slider("Evidence chunks", min_value=2, max_value=10, value=5)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None

    render_overview(corpus)
    render_sample_queries()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    query = st.chat_input("Ask about eligibility, trends, interview rounds, offers, or comparisons")
    if st.session_state.pending_query:
        query = st.session_state.pending_query
        st.session_state.pending_query = None

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        metadata = {
            "company": company.strip() or None,
            "section": section.strip() or None,
        }
        answer, evidence = answer_query(query=query, top_k=top_k, metadata=metadata)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
            render_evidence(evidence)


def render_overview(corpus: list[EvidenceChunk]) -> None:
    if not corpus:
        st.warning("No corpus found. Run the official dataset parser before asking questions.")
        st.code(
            "python -m scripts.parse_dataset --pdf C:\\Users\\SATHVIKA\\Downloads\\Placement_RAG_Dataset_Enhanced.pdf",
            language="powershell",
        )
        return

    sections = pd.Series([chunk.metadata.get("section", "unknown") for chunk in corpus])
    counts = sections.value_counts().rename_axis("section").reset_index(name="records")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Ask the placement corpus")
        st.write(
            "Use the assistant for eligibility filters, package comparisons, interview preparation, trend questions, and conflict checks."
        )
    with col_b:
        st.dataframe(counts, hide_index=True, use_container_width=True)


def render_sample_queries() -> None:
    st.subheader("Judge-style prompts")
    tabs = st.tabs(["Quick checks", "Official set"])

    with tabs[0]:
        columns = st.columns(2)
        for index, query in enumerate(SAMPLE_QUERIES):
            with columns[index % 2]:
                if st.button(query, use_container_width=True):
                    st.session_state.pending_query = query
                    st.rerun()

    with tabs[1]:
        selected = st.selectbox(
            "Official evaluation question",
            OFFICIAL_EVALUATION_QUERIES,
            format_func=lambda item: f"{item['id']} - {item['query']}",
        )
        if st.button("Ask selected question", use_container_width=True):
            st.session_state.pending_query = selected["query"]
            st.rerun()


def answer_query(
    query: str,
    top_k: int,
    metadata: dict[str, str | int | float | None],
) -> tuple[str, list[EvidenceChunk]]:
    request = RetrievalRequest(query=query, top_k=top_k, metadata=metadata)
    evidence = retrieve_context(request)
    answer = generate_answer(query=query, evidence=evidence)
    return answer, evidence


def render_evidence(evidence: list[EvidenceChunk]) -> None:
    if not evidence:
        return

    with st.expander("Retrieved evidence", expanded=False):
        rows = [
            {
                "section": chunk.metadata.get("section", "unknown"),
                "company": chunk.metadata.get("company", ""),
                "source": chunk.source,
                "score": chunk.metadata.get("semantic_score", ""),
                "text": chunk.text,
            }
            for chunk in evidence
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def save_uploaded_files(uploaded_files) -> list[Path]:
    saved_paths: list[Path] = []
    for uploaded_file in uploaded_files:
        target_dir = upload_target_dir(uploaded_file.name)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / uploaded_file.name
        with target_path.open("wb") as file:
            shutil.copyfileobj(uploaded_file, file)
        saved_paths.append(target_path)
    return saved_paths


def upload_target_dir(filename: str) -> Path:
    suffix = Path(filename).suffix.casefold()
    if suffix == ".pdf":
        return DATA_DIR / "pdfs"
    if suffix in {".csv", ".xlsx", ".xls"}:
        return DATA_DIR / "tables"
    return DATA_DIR / "images"


if __name__ == "__main__":
    main()
