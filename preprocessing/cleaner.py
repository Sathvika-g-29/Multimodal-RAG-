import re


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    cleaned = text.replace("\x00", " ")
    return _WHITESPACE_RE.sub(" ", cleaned).strip()

