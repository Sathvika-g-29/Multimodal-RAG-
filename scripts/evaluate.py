import argparse

from evaluation.runner import run_evaluation, summarize_results, write_evaluation_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the official placement RAG evaluation queries.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", default="data/extracted/evaluation_report.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_evaluation(top_k=args.top_k)
    write_evaluation_report(results, args.output)
    summary = summarize_results(results)

    print(f"Evaluated {len(results)} official queries")
    print(f"Classification summary: {summary['by_classification']}")
    print(f"Difficulty summary: {summary['by_difficulty']}")
    print(f"Wrote report to {args.output}")


if __name__ == "__main__":
    main()

