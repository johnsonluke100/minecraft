#!/usr/bin/env python3
"""
quadrant_channel_splitter.py — split LIGHT/SHADE/COLOR channels.

Focus:

  • Read screen_colormap_8xd.json:
       {
         "meta": { ... },
         "checker": [...],
         "LIGHT": [...],
         "SHADE": [...],
         "COLOR": [...]
       }
  • Write three separate JSON files:
       light_quarter_8xd.json
       shade_quarter_8xd.json
       color_quarter_8xd.json
    each containing only:
       {
         "width_quarter": ...,
         "height_quarter": ...,
         "frameIndex": ...,
         "data": [ [0..1], ... ]
       }

This makes it easy for any further processing layer to treat LIGHT/SHADE/COLOR
as distinct 0–1 fields, while still only touching 1/4 of the pixel grid.
"""

import json
import os
from typing import Dict, Any

ROOT = os.path.dirname(os.path.abspath(__file__))
IN_JSON = os.path.join(ROOT, "screen_colormap_8xd.json")
LIGHT_JSON = os.path.join(ROOT, "light_quarter_8xd.json")
SHADE_JSON = os.path.join(ROOT, "shade_quarter_8xd.json")
COLOR_JSON = os.path.join(ROOT, "color_quarter_8xd.json")


def load_colormaps() -> Dict[str, Any]:
    if not os.path.isfile(IN_JSON):
        raise FileNotFoundError(
            "screen_colormap_8xd.json is missing. "
            "Run screen_colormap_generator.py first."
        )
    with open(IN_JSON, "r") as f:
        return json.load(f)


def write_channel(meta: Dict[str, Any], data, out_path: str, label: str) -> None:
    payload = {
        "width_quarter": meta["width_quarter"],
        "height_quarter": meta["height_quarter"],
        "frameIndex": meta["frameIndex"],
        "channel": label,
        "data": data,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    maps = load_colormaps()
    meta = maps["meta"]
    light = maps["LIGHT"]
    shade = maps["SHADE"]
    color = maps["COLOR"]

    write_channel(meta, light, LIGHT_JSON, "LIGHT")
    write_channel(meta, shade, SHADE_JSON, "SHADE")
    write_channel(meta, color, COLOR_JSON, "COLOR")

    print("8XD quadrant channels split:")
    print("  LIGHT →", LIGHT_JSON)
    print("  SHADE →", SHADE_JSON)
    print("  COLOR →", COLOR_JSON)
    print("Quarter size:",
          meta["width_quarter"],
          "x",
          meta["height_quarter"],
          "frame", meta["frameIndex"])


if __name__ == "__main__":
    main()
