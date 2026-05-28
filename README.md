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
- Rule-based reasoning for filtering, sorting, trends, and conflicts
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

The UI shows corpus/index status, official evaluation prompts, retrieval controls, and expandable evidence for each answer.

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

## Build Semantic Index

After `corpus.jsonl` exists, build the FAISS index:

```bash
python -m scripts.build_index
```

This creates generated files under `data/extracted/` and retrieval will use semantic search when those files are present.

## Evaluate

Run the official 30-query evaluation set from the dataset:

```bash
python -m scripts.evaluate
```

The command writes `data/extracted/evaluation_report.json` with answers, evidence sections, and a lightweight response classification.

## Engineering Notes

- The assistant should cite retrieved chunks instead of answering from memory.
- Conflicting evidence is surfaced instead of silently merged.
- Eligibility queries should use metadata filters before generation.
- Unsupported live-data queries should be routed to tools or refused clearly.
- Evaluation queries live in `evaluation/test_queries.py` and should be expanded
  whenever a new data modality is added.
