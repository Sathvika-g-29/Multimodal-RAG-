import argparse

from vectordb.index_builder import build_faiss_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a FAISS semantic index from corpus.jsonl.")
    parser.add_argument("--corpus", default="data/extracted/corpus.jsonl")
    parser.add_argument("--index", default="data/extracted/corpus.faiss")
    parser.add_argument("--manifest", default="data/extracted/corpus_manifest.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = build_faiss_index(
        corpus_path=args.corpus,
        index_path=args.index,
        manifest_path=args.manifest,
    )
    print(f"Indexed {count} corpus records into {args.index}")


if __name__ == "__main__":
    main()

