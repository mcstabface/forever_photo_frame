import json
import os
from pathlib import Path
from typing import Any

from PIL import Image


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_json(path)


def atomic_save_image(image: Image.Image, path: Path) -> None:
    temp_path = path.with_suffix(".tmp.png")
    image.save(temp_path, format="PNG")
    os.replace(temp_path, path)
