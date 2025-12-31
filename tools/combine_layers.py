"""Combine layered PNG assets into a single image.

Usage example:
  python tools/combine_layers.py \
    --layers base.png,body.png,eyes.png \
    --output out/pegasus.png
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from PIL import Image


def parse_layers(value: str) -> list[Path]:
    layers = [layer.strip() for layer in value.split(",") if layer.strip()]
    if not layers:
        raise argparse.ArgumentTypeError("At least one layer path is required.")
    return [Path(layer) for layer in layers]


def load_layers(layer_paths: Iterable[Path]) -> list[Image.Image]:
    images: list[Image.Image] = []
    for path in layer_paths:
        if not path.exists():
            raise FileNotFoundError(f"Layer not found: {path}")
        images.append(Image.open(path).convert("RGBA"))
    return images


def combine_layers(layers: list[Image.Image]) -> Image.Image:
    if not layers:
        raise ValueError("No layers provided.")

    base = layers[0].copy()
    for layer in layers[1:]:
        base.alpha_composite(layer)
    return base


def write_output(image: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--layers",
        required=True,
        type=parse_layers,
        help="Comma-separated list of layer file paths, ordered bottom to top.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output PNG path.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    layers = load_layers(args.layers)
    combined = combine_layers(layers)
    write_output(combined, args.output)


if __name__ == "__main__":
    main()
