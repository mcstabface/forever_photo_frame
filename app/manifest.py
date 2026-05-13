from pathlib import Path

from PIL import Image

from app.config import ARTPACK_DIR, STATE_PATH, WORKING_PATH
from app.storage import load_json, save_json


def load_manifest() -> dict:
    return load_json(ARTPACK_DIR / "manifest.json")


def get_image_entry(image_id: str) -> dict:
    manifest = load_manifest()
    for image in manifest["images"]:
        if image["id"] == image_id:
            return image
    raise RuntimeError(f"Image not found: {image_id}")


def active_images_for_mode(mode: str) -> list[dict]:
    manifest = load_manifest()
    return [
        image
        for image in manifest["images"]
        if image["active"] and image["mode"] == mode
    ]


def pick_next_active_image(mode: str, exclude_image_id: str | None = None) -> dict:
    candidates = [
        image
        for image in active_images_for_mode(mode)
        if image["id"] != exclude_image_id
    ]

    if not candidates:
        raise RuntimeError(f"No active images found for mode={mode} excluding {exclude_image_id}")

    return candidates[0]


def pick_next_unused_image(mode: str, used_ids: list[str]) -> tuple[dict, list[str]]:
    candidates = active_images_for_mode(mode)

    if not candidates:
        raise RuntimeError(f"No active images found for mode={mode}")

    unused = [image for image in candidates if image["id"] not in used_ids]

    if unused:
        return unused[0], used_ids

    reset_used_ids: list[str] = []
    return candidates[0], reset_used_ids


def ensure_next_image(state: dict) -> dict:
    if state["next_image"] is None:
        next_entry = pick_next_active_image(
            mode=state["mode"],
            exclude_image_id=state["current_image"],
        )
        state["next_image"] = next_entry["id"]
        save_json(STATE_PATH, state)
        return next_entry

    return get_image_entry(state["next_image"])


def load_current_image(current_path: Path) -> Image.Image:
    if WORKING_PATH.exists():
        try:
            return Image.open(WORKING_PATH).convert("RGB")
        except OSError:
            WORKING_PATH.unlink(missing_ok=True)

    return Image.open(current_path).convert("RGB")


def load_images_from_state(state: dict) -> tuple[dict, dict, Image.Image, Image.Image]:
    current_entry = get_image_entry(state["current_image"])
    next_entry = ensure_next_image(state)

    current_path = ARTPACK_DIR / current_entry["filename"]
    next_path = ARTPACK_DIR / next_entry["filename"]

    current_img = load_current_image(current_path)
    next_img = Image.open(next_path).convert("RGB")

    if current_img.size != next_img.size:
        raise RuntimeError(f"Image sizes differ: {current_img.size} vs {next_img.size}")

    return current_entry, next_entry, current_img, next_img
