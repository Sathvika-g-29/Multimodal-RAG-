import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from evaluation.test_queries import OFFICIAL_EVALUATION_QUERIES
from llm.generator import generate_answer
from retriever.retriever import RetrievalRequest, retrieve_context


@dataclass(frozen=True)
class EvaluationResult:
    id: str
    difficulty: str
    skill: str
    query: str
    answer: str
    classification: str
    evidence_count: int
    evidence_sections: list[str]


def classify_answer(answer: str) -> str:
    normalized = answer.casefold()
    if "conflicting" in normalized or "conflict" in normalized:
        return "conflict-aware"
    if "do not have enough information" in normalized or "out-of" in normalized:
        return "fallback"
    if "no company in this dataset" in normalized:
        return "edge-case"
    if "evidence:" in normalized or "retrieved evidence:" in normalized:
        return "grounded"
    return "unclassified"


def run_evaluation(top_k: int = 5) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []

    for item in OFFICIAL_EVALUATION_QUERIES:
        query = item["query"]
        request = RetrievalRequest(query=query, top_k=top_k, metadata={})
        evidence = retrieve_context(request)
        answer = generate_answer(query=query, evidence=evidence)
        sections = sorted(
            {
                str(chunk.metadata.get("section", "unknown"))
                for chunk in evidence
            }
        )
        results.append(
            EvaluationResult(
                id=item["id"],
                difficulty=item["difficulty"],
                skill=item["skill"],
                query=query,
                answer=answer,
                classification=classify_answer(answer),
                evidence_count=len(evidence),
                evidence_sections=sections,
            )
        )

    return results


def summarize_results(results: list[EvaluationResult]) -> dict[str, dict[str, int]]:
    return {
        "by_classification": dict(Counter(result.classification for result in results)),
        "by_difficulty": dict(Counter(result.difficulty for result in results)),
    }


def write_evaluation_report(
    results: list[EvaluationResult],
    output_path: str | Path = "data/extracted/evaluation_report.json",
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summarize_results(results),
        "results": [asdict(result) for result in results],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

