import argparse
import json
import math
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = PROJECT_ROOT / "artpack" / "inbox"

DEFAULT_NEGATIVE_PROMPT = (
    "text, words, logo, watermark, signature, people, face, hands, animals, anime, cartoon, "
    "glossy, oversaturated, neon, fantasy armor, dramatic explosion, cinematic poster, "
    "sharp digital artifacts, bad anatomy, duplicate objects, cluttered composition"
)

PROMPT_FAMILIES = {
    "weather_memory": "an archival photograph of a quiet storm over a dark sea, distant horizon, soft mist, muted palette, restrained composition, large areas of negative space, aged paper texture, natural grain, no people, no text, museum print",
    "field_notes": "a vintage scientific field plate of an unknown deep sea botanical specimen, ink and faded watercolor, off white paper, precise but slightly uncanny, sparse annotations removed, centered composition, natural imperfections, no text",
    "empty_architecture": "a quiet empty room at dusk, one tall window, soft indirect light, old plaster walls, minimal composition, muted colors, contemplative atmosphere, medium format photograph, no people, no furniture clutter, no text",
    "night_signals": "a distant radio tower in fog at night, small red signal light, empty landscape, dark blue gray palette, long exposure feeling, quiet negative space, photographic grain, no people, no text",
}


def request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def download_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        return response.read()


def build_workflow(
    checkpoint: str,
    positive_prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    seed: int,
    output_prefix: str,
) -> dict[str, Any]:
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint,
            },
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive_prompt,
                "clip": ["1", 1],
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt,
                "clip": ["1", 1],
            },
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": batch_size,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2],
            },
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": output_prefix,
                "images": ["6", 0],
            },
        },
    }


def queue_prompt(server: str, workflow: dict[str, Any]) -> str:
    result = request_json(f"{server}/prompt", {"prompt": workflow})
    return result["prompt_id"]


def wait_for_history(server: str, prompt_id: str, poll_seconds: float) -> dict[str, Any]:
    while True:
        history = request_json(f"{server}/history/{prompt_id}")
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(poll_seconds)


def save_history_images(server: str, history: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    outputs = history.get("outputs", {})
    for node_output in outputs.values():
        for image in node_output.get("images", []):
            params = urllib.parse.urlencode(
                {
                    "filename": image["filename"],
                    "subfolder": image.get("subfolder", ""),
                    "type": image.get("type", "output"),
                }
            )
            image_bytes = download_bytes(f"{server}/view?{params}")
            target_path = output_dir / image["filename"]
            target_path.write_bytes(image_bytes)
            saved_paths.append(target_path)

    return saved_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-generate frame candidate images through a running ComfyUI server.")
    parser.add_argument("--family", choices=sorted(PROMPT_FAMILIES), required=True)
    parser.add_argument("--count", type=int, default=16, help="Total image candidates to generate")
    parser.add_argument("--batch-size", type=int, default=4, help="Images per ComfyUI job")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--checkpoint", default="juggernautXL_ragnarokBy.safetensors")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg", type=float, default=5.5)
    parser.add_argument("--sampler", default="dpmpp_2m")
    parser.add_argument("--scheduler", default="karras")
    parser.add_argument("--negative", default=DEFAULT_NEGATIVE_PROMPT)
    parser.add_argument("--prompt", default=None, help="Override the selected family prompt")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()

    if args.count <= 0:
        raise RuntimeError("--count must be positive")

    if args.batch_size <= 0:
        raise RuntimeError("--batch-size must be positive")

    prompt = args.prompt or PROMPT_FAMILIES[args.family]
    output_dir = INBOX_DIR / args.family
    job_count = math.ceil(args.count / args.batch_size)
    saved: list[Path] = []

    print(f"family: {args.family}")
    print(f"count: {args.count}")
    print(f"batch_size: {args.batch_size}")
    print(f"output_dir: {output_dir}")

    for job_index in range(job_count):
        remaining = args.count - len(saved)
        current_batch_size = min(args.batch_size, remaining)
        seed = random.randint(0, 2**63 - 1)
        output_prefix = f"frame_{args.family}_{job_index + 1:03d}"

        workflow = build_workflow(
            checkpoint=args.checkpoint,
            positive_prompt=prompt,
            negative_prompt=args.negative,
            width=args.width,
            height=args.height,
            batch_size=current_batch_size,
            steps=args.steps,
            cfg=args.cfg,
            sampler=args.sampler,
            scheduler=args.scheduler,
            seed=seed,
            output_prefix=output_prefix,
        )

        prompt_id = queue_prompt(args.server, workflow)
        print(f"queued job {job_index + 1}/{job_count}: prompt_id={prompt_id} seed={seed}")

        history = wait_for_history(args.server, prompt_id, args.poll_seconds)
        saved_paths = save_history_images(args.server, history, output_dir)
        saved.extend(saved_paths)

        for path in saved_paths:
            print(f"saved: {path}")

    print(f"done: saved {len(saved)} image(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
