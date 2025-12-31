"""Batch OpenArt generations from a prompt list.

Usage example:
  OPENART_API_KEY=your_key \
  python tools/openart_batch.py \
    --input prompts.txt \
    --output-dir output/batch/
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Iterable

import requests

from openart_client import DEFAULT_ENDPOINT, build_payload, write_metadata


def read_prompts(path: Path) -> list[str]:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    if not lines:
        raise ValueError(f"No prompts found in {path}")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="File with one prompt per line.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "openart_batch",
        help="Directory to write response metadata.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help="OpenArt generation endpoint URL.",
    )
    parser.add_argument("--model", default="openart-base", help="Model identifier to request.")
    parser.add_argument("--size", default="1024x1024", help="Output size (e.g. 1024x1024).")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for deterministic outputs.")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds.")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait between requests to avoid rate limits.",
    )
    parser.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        help="Limit the number of prompts processed from the input file.",
    )
    return parser


def perform_generation(
    prompt: str,
    args: argparse.Namespace,
    session: requests.Session,
    headers: dict[str, str],
) -> requests.Response:
    payload_args = argparse.Namespace(
        prompt=prompt,
        model=args.model,
        size=args.size,
        seed=args.seed,
    )
    payload = build_payload(payload_args)
    response = session.post(args.endpoint, json=payload, headers=headers, timeout=args.timeout)
    response.raise_for_status()
    return response


def process_prompts(prompts: Iterable[str], args: argparse.Namespace) -> None:
    api_key = os.environ.get("OPENART_API_KEY")
    if not api_key:
        raise SystemExit("OPENART_API_KEY is required to call OpenArt API.")

    session = requests.Session()
    headers = {"Authorization": f"Bearer {api_key}"}

    prompt_list = list(prompts)

    for idx, prompt in enumerate(prompt_list, start=1):
        try:
            response = perform_generation(prompt, args, session, headers)
        except Exception as exc:  # noqa: BLE001
            print(f"[{idx}] Failed for prompt '{prompt}': {exc}")
            continue

        metadata_path = write_metadata(args.output_dir, response)
        print(f"[{idx}] Saved response for '{prompt}' to {metadata_path}")

        if args.delay > 0 and idx < len(prompt_list):
            time.sleep(args.delay)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    prompts = read_prompts(args.input)
    if args.max_prompts is not None:
        prompts = prompts[: args.max_prompts]

    process_prompts(prompts, args)


if __name__ == "__main__":
    main()
