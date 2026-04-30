import math
import random
from typing import Any

from app.config import ARTPACK_DIR, SUPPORTED_TRANSITION_TYPES
from app.storage import load_json, save_json


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


def build_random_runtime(width: int, height: int) -> dict[str, int]:
    total_pixels = width * height

    if total_pixels <= 0:
        raise RuntimeError("Image dimensions must be positive")

    if total_pixels == 1:
        return {
            "seed": random.getrandbits(64),
            "offset": 0,
            "stride": 1,
        }

    seed = random.getrandbits(64)
    rng = random.Random(seed)

    offset = rng.randrange(total_pixels)
    stride = rng.randrange(1, total_pixels)

    while math.gcd(stride, total_pixels) != 1:
        stride += 1
        if stride >= total_pixels:
            stride = 1

    return {
        "seed": seed,
        "offset": offset,
        "stride": stride,
    }


def ensure_transition(state: dict, state_path, width: int, height: int) -> dict:
    transition_changed = False

    if state["transition"] is None:
        state["transition"] = pick_transition()
        transition_changed = True

    transition = state["transition"]

    if transition["type"] == "random" and "runtime" not in transition:
        transition["runtime"] = build_random_runtime(width, height)
        transition_changed = True

    if transition_changed:
        save_json(state_path, state)

    return transition


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
    runtime: dict[str, int],
    width: int,
    height: int,
) -> tuple[int, int]:
    total_pixels = width * height

    if queue_index >= total_pixels:
        raise IndexError("queue_index out of range")

    offset = runtime["offset"]
    stride = runtime["stride"]

    pixel_index = (offset + (queue_index * stride)) % total_pixels
    x = pixel_index % width
    y = pixel_index // width
    return (x, y)


def pixel_for_transition(
    transition: dict[str, Any],
    queue_index: int,
    width: int,
    height: int,
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
        runtime = transition.get("runtime")
        if runtime is None:
            raise RuntimeError("Random transition requires runtime parameters")
        return pixel_for_random(
            queue_index=queue_index,
            runtime=runtime,
            width=width,
            height=height,
        )

    raise RuntimeError(f"Unsupported transition type: {transition_type}")
