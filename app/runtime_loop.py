import json
import os
import random
import time
from pathlib import Path
from typing import Any

from PIL import Image
from inky.auto import auto


BASE_DIR = Path.home() / "photoframe"
ARTPACK_DIR = BASE_DIR / "artpack"
STATE_DIR = BASE_DIR / "state"

STATE_PATH = STATE_DIR / "state.json"
QUEUE_PATH = STATE_DIR / "queue.json"
WORKING_PATH = STATE_DIR / "working_current_runtime.png"

TICK_SECONDS = 0.01
REFRESH_EVERY_TICKS = 12000

SUPPORTED_TRANSITION_TYPES = {"sweep", "random"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_json(path)


def atomic_save_image(image: Image.Image, path: Path) -> None:
    temp_path = path.with_suffix(".tmp.png")
    image.save(temp_path, format="PNG")
    os.replace(temp_path, path)


def load_manifest() -> dict:
    return load_json(ARTPACK_DIR / "manifest.json")


def get_image_entry(image_id: str) -> dict:
    manifest = load_manifest()
    for image in manifest["images"]:
        if image["id"] == image_id:
            return image
    raise RuntimeError(f"Image not found: {image_id}")


def pick_next_active_image(mode: str, exclude_image_id: str | None = None) -> dict:
    manifest = load_manifest()
    candidates = [
        image
        for image in manifest["images"]
        if image["active"] and image["mode"] == mode and image["id"] != exclude_image_id
    ]

    if not candidates:
        raise RuntimeError(f"No active images found for mode={mode} excluding {exclude_image_id}")

    return candidates[0]


def load_transition_defs() -> list[dict]:
    transitions_dir = ARTPACK_DIR / "transitions"
    transitions: list[dict] = []

    for path in sorted(transitions_dir.glob("*.json")):
        transitions.append(load_json(path))

    if not transitions:
        raise RuntimeError("No transition definitions found")

    return transitions


def pick_transition() -> dict:
    transitions = load_transition_defs()
    supported = [
        transition
        for transition in transitions
        if transition.get("type") in SUPPORTED_TRANSITION_TYPES
    ]

    if not supported:
        raise RuntimeError("No supported transition definitions found")

    weights = [transition.get("weight", 1) for transition in supported]
    return random.choices(supported, weights=weights, k=1)[0]


def build_random_queue(width: int, height: int) -> dict[str, Any]:
    pixels = [(x, y) for y in range(height) for x in range(width)]
    random.shuffle(pixels)
    return {
        "type": "random",
        "width": width,
        "height": height,
        "pixels": pixels,
    }


def load_or_create_random_queue(width: int, height: int) -> dict[str, Any]:
    queue_data = load_optional_json(QUEUE_PATH)

    if queue_data is None:
        queue_data = build_random_queue(width, height)
        save_json(QUEUE_PATH, queue_data)

    return queue_data


def pixel_for_sweep(
    queue_index: int,
    axis: str,
    direction: str,
    width: int,
    height: int,
) -> tuple[int, int]:
    if queue_index >= width * height:
        raise IndexError("queue_index out of range")

    if axis == "x":
        x = queue_index // height
        y = queue_index % height
        if direction == "desc":
            x = (width - 1) - x
        return (x, y)

    if axis == "y":
        y = queue_index // width
        x = queue_index % width
        if direction == "desc":
            y = (height - 1) - y
        return (x, y)

    raise ValueError(f"Unsupported axis: {axis}")


def pixel_for_random(
    queue_index: int,
    queue_data: dict[str, Any],
    width: int,
    height: int,
) -> tuple[int, int]:
    if queue_data["type"] != "random":
        raise RuntimeError(f"Queue type is not random: {queue_data['type']}")

    if queue_data["width"] != width or queue_data["height"] != height:
        raise RuntimeError(
            "Random queue dimensions do not match image size: "
            f"{queue_data['width']}x{queue_data['height']} vs {width}x{height}"
        )

    pixels = queue_data["pixels"]

    if queue_index >= len(pixels):
        raise IndexError("queue_index out of range")

    x, y = pixels[queue_index]
    return (x, y)


def pixel_for_transition(
    transition: dict[str, Any],
    queue_index: int,
    width: int,
    height: int,
    queue_data: dict[str, Any] | None = None,
) -> tuple[int, int]:
    transition_type = transition["type"]

    if transition_type == "sweep":
        return pixel_for_sweep(
            queue_index=queue_index,
            axis=transition["params"]["axis"],
            direction=transition["params"]["direction"],
            width=width,
            height=height,
        )

    if transition_type == "random":
        if queue_data is None:
            raise RuntimeError("Random transition requires queue data")
        return pixel_for_random(
            queue_index=queue_index,
            queue_data=queue_data,
            width=width,
            height=height,
        )

    raise RuntimeError(f"Unsupported transition type: {transition_type}")


def load_current_image(current_path: Path) -> Image.Image:
    if WORKING_PATH.exists():
        try:
            return Image.open(WORKING_PATH).convert("RGB")
        except OSError:
            WORKING_PATH.unlink(missing_ok=True)

    return Image.open(current_path).convert("RGB")


def ensure_next_image(state: dict[str, Any]) -> dict:
    if state["next_image"] is None:
        next_entry = pick_next_active_image(
            mode=state["mode"],
            exclude_image_id=state["current_image"],
        )
        state["next_image"] = next_entry["id"]
        save_json(STATE_PATH, state)
        return next_entry

    return get_image_entry(state["next_image"])


def ensure_transition(state: dict[str, Any]) -> dict:
    if state["transition"] is None:
        state["transition"] = pick_transition()
        save_json(STATE_PATH, state)

    return state["transition"]


def load_images_from_state(state: dict[str, Any]) -> tuple[dict, dict, Image.Image, Image.Image]:
    current_entry = get_image_entry(state["current_image"])
    next_entry = ensure_next_image(state)

    current_path = ARTPACK_DIR / current_entry["filename"]
    next_path = ARTPACK_DIR / next_entry["filename"]

    current_img = load_current_image(current_path)
    next_img = Image.open(next_path).convert("RGB")

    if current_img.size != next_img.size:
        raise RuntimeError(f"Image sizes differ: {current_img.size} vs {next_img.size}")

    return current_entry, next_entry, current_img, next_img


def persist_refresh_frame(display: Any, current_img: Image.Image) -> None:
    atomic_save_image(current_img, WORKING_PATH)
    display.set_image(current_img)
    display.show()


def complete_transition(state: dict[str, Any], current_img: Image.Image, display: Any) -> None:
    persist_refresh_frame(display, current_img)

    completed_image_id = state["next_image"]
    completed_mode = state["mode"]

    state["current_image"] = completed_image_id
    state["queue_index"] = 0

    if completed_mode == "color":
        if completed_image_id not in state["used_color"]:
            state["used_color"].append(completed_image_id)
        state["mode"] = "monochrome"
    elif completed_mode == "monochrome":
        if completed_image_id not in state["used_monochrome"]:
            state["used_monochrome"].append(completed_image_id)
        state["mode"] = "color"

    next_entry = pick_next_active_image(
        mode=state["mode"],
        exclude_image_id=state["current_image"],
    )
    state["next_image"] = next_entry["id"]
    state["transition"] = None

    save_json(STATE_PATH, state)

    if QUEUE_PATH.exists():
        QUEUE_PATH.unlink()

    print("transition complete")


def main() -> None:
    state = load_json(STATE_PATH)
    _, _, current_img, next_img = load_images_from_state(state)

    width, height = current_img.size
    total_pixels = width * height

    transition = ensure_transition(state)
    queue_data = None

    if transition["type"] == "random":
        queue_data = load_or_create_random_queue(width, height)

    current_px = current_img.load()
    next_px = next_img.load()

    display = auto()

    while state["queue_index"] < total_pixels:
        queue_index = state["queue_index"]

        x, y = pixel_for_transition(
            transition=transition,
            queue_index=queue_index,
            width=width,
            height=height,
            queue_data=queue_data,
        )

        current_px[x, y] = next_px[x, y]
        state["queue_index"] += 1
        save_json(STATE_PATH, state)

        if state["queue_index"] % REFRESH_EVERY_TICKS == 0:
            persist_refresh_frame(display, current_img)
            print(f"refreshed at queue_index={state['queue_index']} pixel=({x}, {y})")

        time.sleep(TICK_SECONDS)

    complete_transition(state, current_img, display)


if __name__ == "__main__":
    main()