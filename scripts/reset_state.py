import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_PATH = STATE_DIR / "state.json"
QUEUE_PATH = STATE_DIR / "queue.json"
WORKING_PATH = STATE_DIR / "working_current_runtime.png"
MOCK_PREVIEW_PATH = STATE_DIR / "mock_display_preview.png"


DEFAULT_STATE = {
    "current_image": "c_0001",
    "next_image": None,
    "mode": "color",
    "transition": None,
    "queue_index": 0,
    "used_color": [],
    "used_monochrome": [],
}


def main() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(DEFAULT_STATE, indent=2), encoding="utf-8")

    removed = []
    for path in (QUEUE_PATH, WORKING_PATH, MOCK_PREVIEW_PATH):
        if path.exists():
            path.unlink()
            removed.append(str(path))

    print(f"reset: {STATE_PATH}")
    print("wrote default state:")
    print(json.dumps(DEFAULT_STATE, indent=2))
    print("removed transient files:")
    for path in removed:
        print(f"  - {path}")


if __name__ == "__main__":
    main()