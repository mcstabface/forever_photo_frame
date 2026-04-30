from pathlib import Path

from config import ARTPACK_DIR, STATE_PATH
from manifest import get_image_entry, load_manifest


REQUIRED_STATE_KEYS = {
    "current_image",
    "next_image",
    "mode",
    "transition",
    "queue_index",
    "used_color",
    "used_monochrome",
}


def validate_state_shape(state: dict) -> None:
    missing = REQUIRED_STATE_KEYS - set(state.keys())
    if missing:
        raise RuntimeError(f"state.json missing required keys: {sorted(missing)}")

    if state["mode"] not in {"color", "monochrome"}:
        raise RuntimeError(f"state.json has invalid mode: {state['mode']}")

    if not isinstance(state["queue_index"], int) or state["queue_index"] < 0:
        raise RuntimeError("state.json queue_index must be a non-negative integer")

    if not isinstance(state["used_color"], list) or not isinstance(state["used_monochrome"], list):
        raise RuntimeError("state.json used_color and used_monochrome must be lists")


def validate_manifest_shape(manifest: dict) -> None:
    if "images" not in manifest or not isinstance(manifest["images"], list) or not manifest["images"]:
        raise RuntimeError("manifest.json must contain a non-empty images list")


def validate_image_entry_files(image_entry: dict) -> None:
    required = {"id", "mode", "filename", "width", "height", "active"}
    missing = required - set(image_entry.keys())
    if missing:
        raise RuntimeError(f"manifest image entry missing required keys: {sorted(missing)}")

    image_path = ARTPACK_DIR / image_entry["filename"]
    if not image_path.exists():
        raise RuntimeError(f"Image file not found for manifest entry {image_entry['id']}: {image_path}")


def validate_transition_files() -> None:
    transitions_dir = ARTPACK_DIR / "transitions"
    files = sorted(transitions_dir.glob("*.json"))
    if not files:
        raise RuntimeError(f"No transition definitions found in {transitions_dir}")


def validate_runtime_inputs(state: dict) -> None:
    if not STATE_PATH.exists():
        raise RuntimeError(f"Missing runtime state file: {STATE_PATH}")

    validate_state_shape(state)

    manifest = load_manifest()
    validate_manifest_shape(manifest)

    current_entry = get_image_entry(state["current_image"])
    validate_image_entry_files(current_entry)

    if state["next_image"] is not None:
        next_entry = get_image_entry(state["next_image"])
        validate_image_entry_files(next_entry)

    for image in manifest["images"]:
        validate_image_entry_files(image)

    validate_transition_files()
