"""Generate assets via OpenArt API.

Usage example:
  OPENART_API_KEY=your_key \
  python tools/openart_client.py \
    --prompt "Pegasus with nebula wings" \
    --output-dir output/
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path
from typing import Any

import requests

DEFAULT_ENDPOINT = "https://openart.ai/api/v1/generate"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="Text prompt to generate.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to write generation metadata.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help="OpenArt generation endpoint URL.",
    )
    parser.add_argument(
        "--model",
        default="openart-base",
        help="Model identifier to request.",
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        help="Output size (e.g. 1024x1024).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for deterministic outputs.",
    )
    return parser


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": args.prompt,
        "model": args.model,
        "size": args.size,
    }
    if args.seed is not None:
        payload["seed"] = args.seed
    return payload


def write_metadata(output_dir: Path, response: requests.Response) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = response.headers.get("date", "response")
    safe_name = timestamp.replace(" ", "_").replace(":", "-")
    unique_suffix = uuid.uuid4().hex[:8]
    output_path = output_dir / f"openart_{safe_name}_{unique_suffix}.json"
    output_path.write_text(json.dumps(response.json(), indent=2))
    return output_path


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.environ.get("OPENART_API_KEY")
    if not api_key:
        raise SystemExit("OPENART_API_KEY is required to call OpenArt API.")

    payload = build_payload(args)
    response = requests.post(
        args.endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
    )
    response.raise_for_status()
    output_path = write_metadata(args.output_dir, response)
    print(f"Saved response metadata to {output_path}")


if __name__ == "__main__":
    main()
