import json
from hashlib import sha256
from pathlib import Path


DEFAULT_REGISTRY_PATH = "data/extracted/file_registry.json"


def file_sha256(path: str | Path) -> str:
    file_path = Path(path)
    digest = sha256()
    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, dict[str, str]]:
    registry_path = Path(path)
    if not registry_path.exists():
        return {}
    return json.loads(registry_path.read_text(encoding="utf-8"))


def save_registry(
    registry: dict[str, dict[str, str]],
    path: str | Path = DEFAULT_REGISTRY_PATH,
) -> None:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def register_file(
    file_path: str | Path,
    registry: dict[str, dict[str, str]],
) -> tuple[str, bool]:
    path = Path(file_path)
    digest = file_sha256(path)
    already_seen = digest in registry
    if not already_seen:
        registry[digest] = {
            "path": str(path),
            "name": path.name,
        }
    return digest, already_seen

