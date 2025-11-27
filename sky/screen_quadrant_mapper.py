#!/usr/bin/env python3
"""
screen_quadrant_mapper.py — 8XD quadrant frame ping mapper (Layer 3).

Focus:

  • Read player_resolution.json:
       { "width": W, "height": H, "frameIndex": ... }
  • Read screen_quadrant_request.json:
       { "player": "...", "uuid": "...", "width": W, "height": H, "frameIndex": N }
  • Compute only a quarter grid for TOP_LEFT (base tile).
  • Define 4 quadrants with 3 modes: LIGHT, SHADE, COLOR.
  • Dump screen_quadrant_layout.json for Java + NumPy.

We still only compute 1/4 of the pixel count per frame (conceptually):
  - quarter width  = W / 2
  - quarter height = H / 2

The remaining 3 quadrants mirror or transform this base tile logically.
"""

import json
import os
from typing import Dict, Any

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
PLAYER_RES_JSON = os.path.join(ROOT, "..", "player_resolution.json")
REQ_JSON = os.path.join(ROOT, "..", "screen_quadrant_request.json")
OUT_JSON = os.path.join(ROOT, "screen_quadrant_layout.json")


def load_json(path: str, default: Dict[str, Any]) -> Dict[str, Any]:
    if os.path.isfile(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def load_resolution() -> Dict[str, Any]:
    return load_json(
        PLAYER_RES_JSON,
        {"width": 1920, "height": 1080, "frameIndex": 0},
    )


def load_request() -> Dict[str, Any]:
    return load_json(
        REQ_JSON,
        {"player": "Unknown", "uuid": "", "width": 1920, "height": 1080, "frameIndex": 0},
    )


def compute_quarter_grid(width: int, height: int) -> Dict[str, Any]:
    q_width = max(1, width // 2)
    q_height = max(1, height // 2)

    u = np.linspace(0.0, 0.5, num=q_width, endpoint=False, dtype=np.float64)
    v = np.linspace(0.0, 0.5, num=q_height, endpoint=False, dtype=np.float64)

    uu, vv = np.meshgrid(u, v)

    base_tile = {
        "width": int(q_width),
        "height": int(q_height),
        "u_min": float(u.min()),
        "u_max": float(u.max()),
        "v_min": float(v.min()),
        "v_max": float(v.max()),
        "sample_count": int(uu.size),
    }
    return base_tile


def build_layout(res: Dict[str, Any], req: Dict[str, Any]) -> Dict[str, Any]:
    width = int(res.get("width", 1920))
    height = int(res.get("height", 1080))

    frame_index = int(req.get("frameIndex", 0))
    player = str(req.get("player", "Unknown"))
    uuid = str(req.get("uuid", ""))

    quarter = compute_quarter_grid(width, height)

    layout = {
        "resolution": {"width": width, "height": height},
        "frameIndex": frame_index,
        "player": player,
        "uuid": uuid,
        "quarter": quarter,
        "quadrants": {
            "TOP_LEFT": {
                "mode": "LIGHT",
                "u_range": [0.0, 0.5],
                "v_range": [0.0, 0.5],
            },
            "TOP_RIGHT": {
                "mode": "SHADE",
                "u_range": [0.5, 1.0],
                "v_range": [0.0, 0.5],
            },
            "BOTTOM_LEFT": {
                "mode": "COLOR",
                "u_range": [0.0, 0.5],
                "v_range": [0.5, 1.0],
            },
            "BOTTOM_RIGHT": {
                "mode": "COLOR",
                "u_range": [0.5, 1.0],
                "v_range": [0.5, 1.0],
            },
        },
    }
    return layout


def main() -> None:
    res = load_resolution()
    req = load_request()
    layout = build_layout(res, req)

    with open(OUT_JSON, "w") as f:
        json.dump(layout, f, indent=2)

    print("8XD screen quadrant layout written:")
    print("  Path   :", OUT_JSON)
    print("  Player :", layout.get("player"), layout.get("uuid"))
    print("  Res    :", layout["resolution"]["width"], "x", layout["resolution"]["height"])
    q = layout["quarter"]
    print("  1/4    :", q["width"], "x", q["height"], "samples:", q["sample_count"])
    print("  Frame  :", layout["frameIndex"])
    print("Quadrant modes: LIGHT (TL), SHADE (TR), COLOR (BL/BR).")


if __name__ == "__main__":
    main()
