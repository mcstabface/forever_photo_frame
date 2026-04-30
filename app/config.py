from pathlib import Path


BASE_DIR = Path.home() / "photoframe"
ARTPACK_DIR = BASE_DIR / "artpack"
STATE_DIR = BASE_DIR / "state"

STATE_PATH = STATE_DIR / "state.json"
QUEUE_PATH = STATE_DIR / "queue.json"
WORKING_PATH = STATE_DIR / "working_current_runtime.png"

TICK_SECONDS = 0.01
REFRESH_EVERY_TICKS = 12000

SUPPORTED_TRANSITION_TYPES = {"sweep", "random"}
