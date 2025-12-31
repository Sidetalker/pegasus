"""Download image assets referenced in OpenArt metadata JSON files.

Usage example:
  OPENART_API_KEY=your_key \
  python tools/openart_download_images.py \
    --metadata output/openart_*.json \
    --output-dir output/images/
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests


def looks_like_image(url: str) -> bool:
    lowered = url.lower()
    return lowered.startswith("http") and any(
        lowered.split("?", 1)[0].endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")
    )


def extract_image_urls(payload: object) -> list[str]:
    urls: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, str):
            if looks_like_image(value):
                urls.append(value)
            return
        if isinstance(value, dict):
            url_value = value.get("url")
            if isinstance(url_value, str) and looks_like_image(url_value):
                urls.append(url_value)
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def resolve_files(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        if any(char in pattern for char in "*?[]"):
            files.extend(Path().glob(pattern))
        else:
            files.append(Path(pattern))
    if not files:
        raise FileNotFoundError("No metadata files matched the provided patterns.")
    return files


def build_output_path(output_dir: Path, metadata_file: Path, url: str, index: int) -> Path:
    name = Path(urlsplit(url).path).name
    if not name:
        name = f"{metadata_file.stem}_{index}.png"
    destination = output_dir / name
    if destination.exists():
        destination = output_dir / f"{metadata_file.stem}_{index}_{name}"
    return destination


def download_image(url: str, destination: Path, headers: dict[str, str], timeout: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, headers=headers, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata",
        nargs="+",
        required=True,
        help="Metadata JSON paths or glob patterns produced by openart_client/openart_batch.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "openart_images",
        help="Directory to write downloaded images.",
    )
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds.")
    parser.add_argument(
        "--use-api-key",
        action="store_true",
        help="Include Authorization header using OPENART_API_KEY when downloading.",
    )
    parser.add_argument(
        "--max-per-file",
        type=int,
        default=None,
        help="Limit number of images downloaded from each metadata file.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    headers: dict[str, str] = {}
    if args.use_api_key:
        api_key = os.environ.get("OPENART_API_KEY")
        if not api_key:
            raise SystemExit("OPENART_API_KEY is required when --use-api-key is set.")
        headers["Authorization"] = f"Bearer {api_key}"

    metadata_files = resolve_files(args.metadata)
    for metadata_path in metadata_files:
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to read metadata {metadata_path}: {exc}")
            continue

        urls = extract_image_urls(payload)
        if not urls:
            print(f"No image URLs found in {metadata_path}")
            continue

        if args.max_per_file is not None:
            urls = urls[: args.max_per_file]

        for index, url in enumerate(urls, start=1):
            destination = build_output_path(args.output_dir, metadata_path, url, index)
            try:
                download_image(url, destination, headers, args.timeout)
            except Exception as exc:  # noqa: BLE001
                print(f"Failed to download {url} from {metadata_path}: {exc}")
                continue

            print(f"Saved {url} -> {destination}")


if __name__ == "__main__":
    main()
