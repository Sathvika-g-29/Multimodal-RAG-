from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ImageDocument:
    source_path: str
    width: int
    height: int


def load_image(image_path: str | Path) -> ImageDocument:
    path = Path(image_path)
    with Image.open(path) as image:
        width, height = image.size
    return ImageDocument(source_path=str(path), width=width, height=height)

