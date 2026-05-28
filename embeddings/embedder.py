from functools import lru_cache
import os
from pathlib import Path

from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CACHE_DIR = "data/extracted/model_cache"


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    cache_dir = Path(os.getenv("MODEL_CACHE_DIR", DEFAULT_CACHE_DIR))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return SentenceTransformer(model_name, cache_folder=str(cache_dir))


def embed_texts(texts: list[str], model_name: str = DEFAULT_MODEL) -> list[list[float]]:
    model = get_embedding_model(model_name)
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()
