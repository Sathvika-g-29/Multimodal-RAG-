# Multimodal Placement Intelligence Assistant

A retrieval-augmented assistant for placement analytics across structured tables,
interview narratives, extracted chart/image content, and temporal trend data.

The goal is to answer placement-related questions with grounded evidence, explicit
eligibility filtering, and graceful refusal for unsupported or out-of-scope prompts.

## Current Scope

- PDF text extraction with source metadata
- Table extraction pipeline interface
- OCR/image-caption ingestion interface
- Chunking and cleaning utilities
- FAISS-backed vector search
- Metadata-aware retrieval and reranking hooks
- Streamlit chat interface
- Evaluation query set for regression testing

## Architecture

```text
PDFs / datasets / images
        |
        v
Document ingestion
        |
        +-- text extraction
        +-- table extraction
        +-- OCR and chart captioning
        |
        v
Cleaning, deduplication, chunking
        |
        v
Embeddings + FAISS vector store
        |
        v
Hybrid retrieval + metadata filters + reranking
        |
        v
Grounded LLM response
        |
        v
Streamlit UI
```

## Repository Layout

```text
app.py
requirements.txt
.env.example
data/
ingestion/
preprocessing/
embeddings/
vectordb/
retriever/
llm/
tools/
evaluation/
tests/
docs/
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
streamlit run app.py
```

## Build Corpus

Place source files into:

- `data/pdfs/` for placement PDFs
- `data/images/` for charts, screenshots, and image notices
- `data/tables/` for CSV/XLSX placement tables

Then run:

```bash
python -m scripts.ingest
```

This writes normalized source records to `data/extracted/corpus.jsonl`.

For the official hackathon dataset, use the dataset-specific parser instead:

```bash
python -m scripts.parse_dataset --pdf C:\Users\SATHVIKA\Downloads\Placement_RAG_Dataset_Enhanced.pdf
```

This parser avoids embedding evaluation/adversarial questions and creates structured records for eligibility rows,
hiring distribution, trend data, conflicting records, overall statistics, and interview experiences.

## Engineering Notes

- The assistant should cite retrieved chunks instead of answering from memory.
- Conflicting evidence is surfaced instead of silently merged.
- Eligibility queries should use metadata filters before generation.
- Unsupported live-data queries should be routed to tools or refused clearly.
- Evaluation queries live in `evaluation/test_queries.py` and should be expanded
  whenever a new data modality is added.
