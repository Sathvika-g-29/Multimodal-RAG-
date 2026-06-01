import argparse

from vectordb.chroma_index_builder import build_chroma_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a persistent Chroma index from corpus.jsonl.")
    parser.add_argument("--corpus", default="data/extracted/corpus.jsonl")
    parser.add_argument("--persist-path", default="data/extracted/chroma")
    parser.add_argument("--collection", default="placement_corpus")
    parser.add_argument("--incremental", action="store_true", help="Upsert without resetting the collection")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = build_chroma_index(
        corpus_path=args.corpus,
        persist_path=args.persist_path,
        collection_name=args.collection,
        reset=not args.incremental,
    )
    print(f"Indexed {count} corpus records into Chroma collection '{args.collection}'")


if __name__ == "__main__":
    main()
