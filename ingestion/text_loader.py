from dataclasses import dataclass
from pathlib import Path

import pdfplumber


@dataclass(frozen=True)
class ExtractedTextPage:
    source_path: str
    page_number: int
    text: str


def extract_pdf_text(pdf_path: str | Path) -> list[ExtractedTextPage]:
    path = Path(pdf_path)
    pages: list[ExtractedTextPage] = []

    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(
                    ExtractedTextPage(
                        source_path=str(path),
                        page_number=index,
                        text=text.strip(),
                    )
                )

    return pages

