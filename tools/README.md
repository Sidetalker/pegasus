# Tools

Utilities for wiring layered Pegasus assets into final PNGs.

## combine_layers.py

Combines ordered PNG layers into a single image.

### Requirements
- Python 3.10+
- Pillow (`pip install Pillow`)

### Example
```bash
python tools/combine_layers.py \
  --layers assets/base.png,assets/body.png,assets/eyes.png \
  --output output/pegasus.png
```
