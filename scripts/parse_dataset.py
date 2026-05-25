import argparse

from ingestion.enhanced_dataset_parser import parse_enhanced_dataset
from ingestion.pipeline import write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Placement_RAG_Dataset_Enhanced.pdf into structured RAG records."
    )
    parser.add_argument("--pdf", required=True, help="Path to Placement_RAG_Dataset_Enhanced.pdf")
    parser.add_argument("--output", default="data/extracted/corpus.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    documents = parse_enhanced_dataset(args.pdf)
    count = write_jsonl(documents, args.output)
    print(f"Wrote {count} dataset-specific source documents to {args.output}")


if __name__ == "__main__":
    main()

