from dataclasses import asdict, dataclass
from hashlib import sha1


MetadataValue = str | int | float | bool | None


@dataclass(frozen=True)
class SourceDocument:
    id: str
    text: str
    source_path: str
    source_type: str
    metadata: dict[str, MetadataValue]

    @classmethod
    def create(
        cls,
        text: str,
        source_path: str,
        source_type: str,
        metadata: dict[str, MetadataValue] | None = None,
    ) -> "SourceDocument":
        clean_text = text.strip()
        digest_input = f"{source_path}|{source_type}|{clean_text}".encode("utf-8")
        document_id = sha1(digest_input).hexdigest()[:16]
        return cls(
            id=document_id,
            text=clean_text,
            source_path=source_path,
            source_type=source_type,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

