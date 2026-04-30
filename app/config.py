import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = Path(os.environ.get("PHOTOFRAME_HOME", PROJECT_ROOT)).resolve()
ARTPACK_DIR = BASE_DIR / "artpack"
STATE_DIR = BASE_DIR / "state"

STATE_PATH = STATE_DIR / "state.json"
QUEUE_PATH = STATE_DIR / "queue.json"
WORKING_PATH = STATE_DIR / "working_current_runtime.png"
MOCK_PREVIEW_PATH = STATE_DIR / "mock_display_preview.png"

TICK_SECONDS = float(os.environ.get("PHOTOFRAME_TICK_SECONDS", "1"))
REFRESH_EVERY_TICKS = int(os.environ.get("PHOTOFRAME_REFRESH_EVERY_TICKS", "900"))

SUPPORTED_TRANSITION_TYPES = {"sweep", "random"}
