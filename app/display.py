import os
from typing import Any

from inky.auto import auto
from PIL import Image

from config import MOCK_PREVIEW_PATH
from storage import atomic_save_image


class MockDisplay:
    def __init__(self) -> None:
        self._image: Image.Image | None = None

    def set_image(self, image: Image.Image) -> None:
        self._image = image.copy()

    def show(self) -> None:
        if self._image is None:
            raise RuntimeError("MockDisplay.show() called before set_image()")
        atomic_save_image(self._image, MOCK_PREVIEW_PATH)
        print(f"mock display updated: {MOCK_PREVIEW_PATH}")


def get_display() -> Any:
    use_mock = os.environ.get("PHOTOFRAME_USE_MOCK_DISPLAY", "").strip().lower()

    if use_mock in {"1", "true", "yes", "on"}:
        print("using mock display")
        return MockDisplay()

    return auto()
