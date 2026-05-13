import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTPACK_DIR = PROJECT_ROOT / "artpack"
MANIFEST_PATH = ARTPACK_DIR / "manifest.json"
PANEL_SIZE = (1600, 1200)
VALID_MODES = {"color", "monochrome"}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_") or "image"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise RuntimeError(f"manifest not found: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def next_image_id(manifest: dict, mode: str) -> str:
    prefix = "c" if mode == "color" else "m"
    pattern = re.compile(rf"^{prefix}_(\d{{4}})$")

    highest = 0
    for image in manifest.get("images", []):
        match = pattern.match(image.get("id", ""))
        if match:
            highest = max(highest, int(match.group(1)))

    return f"{prefix}_{highest + 1:04d}"


def output_path_for(source_path: Path, mode: str) -> Path:
    mode_dir = ARTPACK_DIR / mode
    mode_dir.mkdir(parents=True, exist_ok=True)

    base_name = slugify(source_path.stem)
    output_path = mode_dir / f"{base_name}_panel_ready.png"

    counter = 2
    while output_path.exists():
        output_path = mode_dir / f"{base_name}_{counter}_panel_ready.png"
        counter += 1

    return output_path


def panel_ready_image(source_path: Path, mode: str) -> Image.Image:
    image = Image.open(source_path)
    image = ImageOps.exif_transpose(image)

    if mode == "monochrome":
        image = image.convert("L").convert("RGB")
    else:
        image = image.convert("RGB")

    return ImageOps.fit(
        image,
        PANEL_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def add_image(source_path: Path, mode: str, active: bool) -> dict:
    if mode not in VALID_MODES:
        raise RuntimeError(f"invalid mode: {mode}; expected one of {sorted(VALID_MODES)}")

    if not source_path.exists():
        raise RuntimeError(f"source image not found: {source_path}")

    manifest = load_manifest()
    manifest.setdefault("version", 1)
    manifest.setdefault("images", [])

    output_path = output_path_for(source_path, mode)
    image = panel_ready_image(source_path, mode)
    image.save(output_path, format="PNG")

    image_id = next_image_id(manifest, mode)
    file_hash = sha256_file(output_path)
    relative_filename = output_path.relative_to(ARTPACK_DIR).as_posix()

    entry = {
        "id": image_id,
        "mode": mode,
        "filename": relative_filename,
        "width": PANEL_SIZE[0],
        "height": PANEL_SIZE[1],
        "sha256": file_hash,
        "format": "png",
        "encrypted": False,
        "used_count": 0,
        "active": active,
    }

    manifest["images"].append(entry)
    save_manifest(manifest)

    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Add a source image to the photoframe artpack.")
    parser.add_argument("source", type=Path, help="Path to the source image")
    parser.add_argument("--mode", required=True, choices=sorted(VALID_MODES), help="Target artpack mode")
    parser.add_argument("--inactive", action="store_true", help="Register the image as inactive")
    parser.add_argument("--copy-source", action="store_true", help="Also copy the original into artpack/<mode>/")
    args = parser.parse_args()

    source_path = args.source.expanduser().resolve()
    entry = add_image(source_path=source_path, mode=args.mode, active=not args.inactive)

    if args.copy_source:
        original_dir = ARTPACK_DIR / args.mode / "source"
        original_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, original_dir / source_path.name)

    print("registered image:")
    print(json.dumps(entry, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
