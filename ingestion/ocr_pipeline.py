from pathlib import Path

import pytesseract
from PIL import Image


def extract_image_text(image_path: str | Path) -> str:
    path = Path(image_path)
    with Image.open(path) as image:
        return pytesseract.image_to_string(image).strip()

