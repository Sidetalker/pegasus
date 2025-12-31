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

## openart_client.py

Posts a prompt to OpenArt and stores the response metadata.

### Requirements
- Python 3.10+
- Requests (`pip install requests`)
- `OPENART_API_KEY` environment variable

### Example
```bash
OPENART_API_KEY=your_key \
python tools/openart_client.py \
  --prompt "Pegasus with nebula wings" \
  --output-dir output/
```

## trait_generation_alternatives.md

Shortlist of other services to evaluate for trait generation.
