from typing import Any
import time

from PIL import Image

from app.config import DISPLAY_SECONDS, QUEUE_PATH, STATE_PATH, WORKING_PATH
from app.display import get_display
from app.manifest import get_image_entry, pick_next_unused_image
from app.storage import atomic_save_image, load_json, save_json
from app.validation import validate_runtime_inputs


def persist_display_frame(display: Any, image: Image.Image) -> None:
    atomic_save_image(image, WORKING_PATH)
    display.set_image(image)
    display.show()


def mark_current_image_used(state: dict[str, Any]) -> None:
    current_image_id = state["current_image"]
    mode = state["mode"]

    if mode == "color":
        if current_image_id not in state["used_color"]:
            state["used_color"].append(current_image_id)
    elif mode == "monochrome":
        if current_image_id not in state["used_monochrome"]:
            state["used_monochrome"].append(current_image_id)


def flip_mode(state: dict[str, Any]) -> None:
    if state["mode"] == "color":
        state["mode"] = "monochrome"
    elif state["mode"] == "monochrome":
        state["mode"] = "color"
    else:
        raise RuntimeError(f"Unsupported mode: {state['mode']}")


def used_key_for_mode(mode: str) -> str:
    if mode == "color":
        return "used_color"
    if mode == "monochrome":
        return "used_monochrome"
    raise RuntimeError(f"Unsupported mode: {mode}")


def prepare_next_cycle(state: dict[str, Any]) -> None:
    mark_current_image_used(state)
    flip_mode(state)

    used_key = used_key_for_mode(state["mode"])
    next_entry, updated_used_ids = pick_next_unused_image(
        mode=state["mode"],
        used_ids=state[used_key],
    )

    state[used_key] = updated_used_ids
    state["current_image"] = next_entry["id"]
    state["next_image"] = None
    state["transition"] = None
    state["queue_index"] = 0

    if QUEUE_PATH.exists():
        QUEUE_PATH.unlink()

    save_json(STATE_PATH, state)


def load_image_for_current_state(state: dict[str, Any]) -> Image.Image:
    current_entry = get_image_entry(state["current_image"])
    image_path = current_entry["filename"]

    from app.config import ARTPACK_DIR

    return Image.open(ARTPACK_DIR / image_path).convert("RGB")


def run_runtime_loop() -> None:
    display = get_display()

    while True:
        state = load_json(STATE_PATH)
        validate_runtime_inputs(state)

        image = load_image_for_current_state(state)
        persist_display_frame(display, image)
        print(f"displayed image={state['current_image']} mode={state['mode']}")

        prepare_next_cycle(state)
        print(f"next image={state['current_image']} mode={state['mode']} after {DISPLAY_SECONDS} seconds")

        time.sleep(DISPLAY_SECONDS)
