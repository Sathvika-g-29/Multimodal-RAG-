import argparse
from pathlib import Path

from ingestion.batch_ingestion import ingest_files_incrementally
from ingestion.pipeline import append_jsonl
from vectordb.chroma_index_builder import build_chroma_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch ingest supported documents with duplicate detection.")
    parser.add_argument("paths", nargs="+", help="Files or folders to ingest")
    parser.add_argument("--output", default="data/extracted/corpus.jsonl")
    parser.add_argument("--update-chroma", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    documents, skipped = ingest_files_incrementally(args.paths)
    count = append_jsonl(documents, args.output)
    print(f"Wrote {count} new source documents to {args.output}")
    print(f"Skipped {len(skipped)} duplicate file(s)")

    if args.update_chroma:
        indexed = build_chroma_index(corpus_path=Path(args.output))
        print(f"Updated Chroma index with {indexed} corpus records")


if __name__ == "__main__":
    main()
