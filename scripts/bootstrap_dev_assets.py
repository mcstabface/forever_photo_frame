import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

STATE_EXAMPLE = PROJECT_ROOT / "state" / "state.example.json"
STATE_LIVE = PROJECT_ROOT / "state" / "state.json"

MANIFEST_EXAMPLE = PROJECT_ROOT / "artpack" / "manifest.example.json"
MANIFEST_LIVE = PROJECT_ROOT / "artpack" / "manifest.json"


def copy_if_missing(src: Path, dst: Path) -> None:
    if dst.exists():
        print(f"exists: {dst}")
        return
    if not src.exists():
        raise RuntimeError(f"missing example file: {src}")
    shutil.copy2(src, dst)
    print(f"created: {dst}")


def main() -> None:
    copy_if_missing(STATE_EXAMPLE, STATE_LIVE)
    copy_if_missing(MANIFEST_EXAMPLE, MANIFEST_LIVE)


if __name__ == "__main__":
    main()