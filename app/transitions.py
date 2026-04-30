import random
from typing import Any

from config import ARTPACK_DIR, QUEUE_PATH, SUPPORTED_TRANSITION_TYPES
from storage import load_json, load_optional_json, save_json


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


def ensure_transition(state: dict, state_path) -> dict:
    if state["transition"] is None:
        state["transition"] = pick_transition()
        save_json(state_path, state)

    return state["transition"]


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
