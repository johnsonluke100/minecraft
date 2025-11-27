#!/usr/bin/env python3
"""
screen_colormap_generator.py — 8XD LIGHT/SHADE/COLOR checker colormaps.

Focus:

  • Read screen_quadrant_layout.json (from screen_quadrant_mapper.py).
  • Build a quarter-tile color field in NumPy:
       - base_color   : a soft gradient in 0–1
       - light_map    : white + color 4-checker
       - shade_map    : black + color 4-checker
       - color_map    : pure color
  • Write screen_colormap_8xd.json with 0–1 floats only.

Quarter tile concept:
  We only compute a Wq × Hq tile for TOP_LEFT. The other three quadrants
  are logical transforms / mirrors of this tile. That keeps total pixel
  computations to 1/4 per frame.
"""

import json
import os
from typing import Dict, Any

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
LAYOUT_JSON = os.path.join(ROOT, "screen_quadrant_layout.json")
OUT_JSON = os.path.join(ROOT, "screen_colormap_8xd.json")


def load_layout() -> Dict[str, Any]:
    if not os.path.isfile(LAYOUT_JSON):
        raise FileNotFoundError(
            "screen_quadrant_layout.json is missing. "
            "Run screen_quadrant_mapper.py first."
        )
    with open(LAYOUT_JSON, "r") as f:
        return json.load(f)


def build_colormaps(layout: Dict[str, Any]) -> Dict[str, Any]:
    q_info = layout["quarter"]
    wq = int(q_info["width"])
    hq = int(q_info["height"])
    frame_index = int(layout.get("frameIndex", 0))

    u = np.linspace(0.0, 0.5, num=wq, endpoint=False, dtype=np.float64)
    v = np.linspace(0.0, 0.5, num=hq, endpoint=False, dtype=np.float64)
    uu, vv = np.meshgrid(u, v)

    center_u = 0.25
    center_v = 0.25
    dist = np.sqrt((uu - center_u) ** 2 + (vv - center_v) ** 2)
    dist_norm = dist / np.max(dist) if np.max(dist) > 0 else dist

    phase = (frame_index % 64) / 64.0
    base_color = np.clip(1.0 - dist_norm + 0.25 * np.sin(2.0 * np.pi * phase), 0.0, 1.0)

    rows = np.arange(hq).reshape(-1, 1)
    cols = np.arange(wq).reshape(1, -1)
    checker = (rows % 2) ^ (cols % 2)
    checker_f = checker.astype(np.float64)

    light_white = 1.0
    light_color_weight = 0.85
    light_white_weight = 0.35

    light_map = np.where(
        checker == 0,
        light_white * light_white_weight + base_color * (1.0 - light_white_weight),
        base_color * light_color_weight + (1.0 - light_color_weight) * 0.9,
    )
    light_map = np.clip(light_map, 0.0, 1.0)

    shade_color_weight = 0.6

    shade_map = np.where(
        checker == 0,
        base_color * 0.25,
        base_color * shade_color_weight + (1.0 - shade_color_weight) * 0.4,
    )
    shade_map = np.clip(shade_map, 0.0, 1.0)

    color_map = base_color.copy()

    def compress(arr: np.ndarray):
        return arr.astype(float).tolist()

    colormaps = {
        "meta": {
            "width_quarter": wq,
            "height_quarter": hq,
            "frameIndex": frame_index,
            "note": "Values 0–1 only. Quarter tile mirrored to 4 quadrants; "
                    "LIGHT / SHADE / COLOR applied per quadrant.",
        },
        "checker": compress(checker_f),
        "LIGHT": compress(light_map),
        "SHADE": compress(shade_map),
        "COLOR": compress(color_map),
    }
    return colormaps


def main() -> None:
    layout = load_layout()
    colormaps = build_colormaps(layout)
    with open(OUT_JSON, "w") as f:
        json.dump(colormaps, f, indent=2)
    print("8XD screen colormaps written:")
    print("  Path :", OUT_JSON)
    print("  Quarter size:",
          colormaps["meta"]["width_quarter"],
          "x",
          colormaps["meta"]["height_quarter"])
    print("  Frame:", colormaps["meta"]["frameIndex"])
    print("LIGHT / SHADE / COLOR checker maps ready.")


if __name__ == "__main__":
    main()
