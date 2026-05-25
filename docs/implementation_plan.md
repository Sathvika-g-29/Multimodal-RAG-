# Implementation Plan

## Milestone 1: Reliable Ingestion

- Extract text from PDFs with page-level metadata.
- Extract tables into normalized CSV/JSON rows.
- Store OCR outputs for charts and image-based notices.
- Preserve source file, page number, modality, company, year, and role.

## Milestone 2: Retrieval Quality

- Chunk text by semantic boundaries where possible.
- Keep table rows as compact factual records.
- Add metadata filters for company, year, degree, branch, CGPA, and role.
- Add reranking for cross-company and multi-hop questions.

## Milestone 3: Grounded Generation

- Generate answers only from retrieved evidence.
- Cite source snippets and expose conflicting facts.
- Refuse out-of-scope or adversarial requests.
- Route arithmetic and CSV aggregation to tools.

## Milestone 4: Evaluation

- Maintain a fixed query set for eligibility, trends, conflict handling,
  chart interpretation, and adversarial prompts.
- Track retrieval precision, answer faithfulness, and refusal quality.

