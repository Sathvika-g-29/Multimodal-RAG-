import argparse

from ingestion.pipeline import build_corpus, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the placement assistant corpus JSONL.")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--image-dir", default="data/images")
    parser.add_argument("--table-dir", default="data/tables")
    parser.add_argument("--output", default="data/extracted/corpus.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    documents = build_corpus(
        pdf_dir=args.pdf_dir,
        image_dir=args.image_dir,
        table_dir=args.table_dir,
    )
    count = write_jsonl(documents, args.output)
    print(f"Wrote {count} source documents to {args.output}")


if __name__ == "__main__":
    main()

