from typing import Any
import time

from PIL import Image

from app.config import QUEUE_PATH, REFRESH_EVERY_TICKS, STATE_PATH, TICK_SECONDS, WORKING_PATH
from app.display import get_display
from app.manifest import load_images_from_state, pick_next_active_image
from app.storage import atomic_save_image, load_json, save_json
from app.transitions import ensure_transition, pixel_for_transition
from app.validation import validate_runtime_inputs


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


def run_runtime_loop() -> None:
    state = load_json(STATE_PATH)
    validate_runtime_inputs(state)
    _, _, current_img, next_img = load_images_from_state(state)

    width, height = current_img.size
    total_pixels = width * height

    transition = ensure_transition(state, STATE_PATH, width, height)

    current_px = current_img.load()
    next_px = next_img.load()

    display = get_display()

    while state["queue_index"] < total_pixels:
        queue_index = state["queue_index"]

        x, y = pixel_for_transition(
            transition=transition,
            queue_index=queue_index,
            width=width,
            height=height,
        )

        current_px[x, y] = next_px[x, y]
        state["queue_index"] += 1
        save_json(STATE_PATH, state)

        if state["queue_index"] % REFRESH_EVERY_TICKS == 0:
            persist_refresh_frame(display, current_img)
            print(f"refreshed at queue_index={state['queue_index']} pixel=({x}, {y})")

        import time
        time.sleep(TICK_SECONDS)

    complete_transition(state, current_img, display)
