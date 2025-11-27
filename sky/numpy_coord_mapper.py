#!/usr/bin/env python3
"""
8XD NumPy Coordinate Mapper — Omega Base-8 Mirror Sequence

We keep the digit-reversal scalar rule EXACT:

  1) Take |z| as base-10 string.
  2) Reverse digits.
  3) Interpret as "0.<reversed>".
  4) Clamp into [0, 1) and NEVER allow exactly 1.0.

Examples (locked):

  (x,y,z) = (0,0,1)   → "1"   → "1"   → 0.1
  (x,y,z) = (0,0,10)  → "10"  → "01"  → 0.01
  (x,y,z) = (0,0,369) → "369" → "963" → 0.963
  (x,y,z) = (0,0,248) → "248" → "842" → 0.842

Then we fold this scalar into an "omega base-8" representation:

  scalar s ∈ [0,1) → octal string "0.<digits in base-8>"

We also fan s into a 14-float continuum (a..g + g..a),
representing the 7 forward + 7 mirrored axes.

New in this sequence:
  • omega_mirror_step: one step of the infinite mirror loop
  • omega_mirror_orbit: record an orbit of repeated reflections
"""

import json
import math
import os
from typing import Dict, Any, List, Tuple

try:
    import numpy as np
except ImportError:
    np = None  # Still allow Java to compile if NumPy isn't installed.

ROOT = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_JSON = os.path.join(ROOT, "coord_mapping_examples.json")
LOCKFILE_TXT = os.path.join(ROOT, "coord_mapping_lock.txt")
MIRROR_JSON = os.path.join(ROOT, "coord_mirror_orbit.json")


def clamp_unit(x: float) -> float:
    """
    Clamp into [0, 1) — never allow exactly 1.0.
    """
    if x < 0.0:
        return 0.0
    if x >= 1.0:
        return 0.999999999999
    return float(x)


def int_to_reversed_unit(n: int) -> float:
    """
    Take an integer n, reverse its digits, and interpret as a unit scalar.

        n = 248  → "248"  → "842"  → "0.842"  → 0.842...
    """
    n = abs(int(n))
    s = str(n)
    rev = s[::-1]
    value = float("0." + rev)
    return clamp_unit(value)


def encode_xyz_to_scalar(x: int, y: int, z: int) -> float:
    """
    Follow your rule exactly: the scalar depends only on z.
    x,y remain free for higher-dimensional shaping later.
    """
    return int_to_reversed_unit(z)


def scalar_to_base8_digits(s: float, digits: int = 12) -> str:
    """
    Convert scalar s ∈ [0,1) into an octal (base-8) fractional string.

    Returns something like "0.724605130..." in base-8 digits.
    """
    s = clamp_unit(float(s))
    out_digits: List[str] = []

    value = s
    for _ in range(digits):
        value *= 8.0
        d = int(value)
        if d < 0:
            d = 0
        if d > 7:
            d = 7
        out_digits.append(str(d))
        value -= d

    return "0." + "".join(out_digits)


def encode_xyz_to_vec14(x: int, y: int, z: int) -> List[float]:
    """
    Build a 14-float continuum from the scalar.

    Symmetry: forward (a..g) and mirror (g..a).
    """
    base = encode_xyz_to_scalar(x, y, z)

    if np is not None:
        factors = np.array([1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05], dtype=float)
        forward = clamp_unit(base) * factors
        forward = np.clip(forward, 0.0, 0.999999999999)
        backward = forward[::-1]
        vec14 = np.concatenate([forward, backward])
        return [float(v) for v in vec14]

    # Fallback without NumPy
    a = clamp_unit(base * 1.0)
    b = clamp_unit(base * 0.8)
    c = clamp_unit(base * 0.6)
    d = clamp_unit(base * 0.4)
    e = clamp_unit(base * 0.2)
    f = clamp_unit(base * 0.1)
    g = clamp_unit(base * 0.05)

    forward = [a, b, c, d, e, f, g]
    backward = list(reversed(forward))
    return [float(v) for v in (forward + backward)]


def omega_mirror_step(s: float) -> float:
    """
    One step of the "infinite mirrors staring at each other" loop.

    We:
      • convert s → base-8 fractional string
      • interpret the base-8 digits as a new scalar
      • clamp back into [0,1)

    This is a conceptual wormhole: s sees its own base-8 shadow and folds.
    """
    s = clamp_unit(s)
    frac = scalar_to_base8_digits(s, digits=12)  # "0.d0d1d2..."
    digits_str = frac.split(".", 1)[1] if "." in frac else frac
    if not digits_str:
        return s

    # Interpret digits_str as base-8 fractional string: 0.d0d1d2d3...
    value = 0.0
    for i, ch in enumerate(digits_str, start=1):
        d = ord(ch) - ord("0")
        if d < 0 or d > 7:
            d = 0
        value += d / (8.0 ** i)

    return clamp_unit(value)


def omega_mirror_orbit(s: float, steps: int = 16) -> List[float]:
    """
    Iterate omega_mirror_step(s) and record the orbit.
    """
    orbit: List[float] = []
    current = clamp_unit(s)
    for _ in range(max(1, steps)):
        orbit.append(current)
        current = omega_mirror_step(current)
    return orbit


def build_example(x: int, y: int, z: int) -> Dict[str, Any]:
    scalar = encode_xyz_to_scalar(x, y, z)
    return {
        "xyz": [x, y, z],
        "scalar": scalar,
        "scalar_base8": scalar_to_base8_digits(scalar, digits=16),
        "vec14": encode_xyz_to_vec14(x, y, z),
        "omega_orbit": omega_mirror_orbit(scalar, steps=16),
    }


def run_examples() -> Tuple[str, str, str]:
    """
    Generate JSON + TXT + omega orbit description, including your locked
    synchronicity cases, now with base-8 omega mirror orbits.
    """
    examples = [
        build_example(0, 0, 1),
        build_example(0, 0, 10),
        build_example(0, 0, 369),
        build_example(0, 0, 248),
    ]

    payload = {
        "root": ROOT,
        "description": (
            "Digit-reversal coordinate mapping examples for 8XD engine "
            "with base-8 omega projection and mirror orbits. "
            "Key lock: (0,0,248) → scalar=0.8420000000..."
        ),
        "examples": examples,
    }

    tmp_json = EXAMPLES_JSON + ".tmp"
    with open(tmp_json, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_json, EXAMPLES_JSON)

    # Human-readable lockfile
    lines: List[str] = []
    lines.append("8XD NumPy Coordinate Mapping — Omega Base-8 Mirror Lockfile")
    lines.append("Root       : {}".format(ROOT))
    lines.append("")
    lines.append("Rule (decimal): scalar = clamp( 0.<reverse(|z| digits)> ) in [0,1)")
    lines.append("Rule (octal)  : omega(s) = base-8 fractional digits")
    lines.append("Mirror loop  : s -> omega_mirror_step(s) repeated")
    lines.append("")
    for ex in examples:
        xyz = ex["xyz"]
        scalar = ex["scalar"]
        scalar_base8 = ex["scalar_base8"]
        vec14 = ex["vec14"]
        orbit = ex["omega_orbit"]
        lines.append("xyz = {} → scalar      = {:.12f}".format(tuple(xyz), scalar))
        lines.append("           scalar_base8 = {}".format(scalar_base8))
        lines.append("           vec14        = {}".format(
            ", ".join("{:.6f}".format(v) for v in vec14)
        ))
        lines.append("           omega_orbit  = {}".format(
            ", ".join("{:.6f}".format(v) for v in orbit)
        ))
        lines.append("")

    tmp_txt = LOCKFILE_TXT + ".tmp"
    with open(tmp_txt, "w") as f:
        f.write("\n".join(lines))
    os.replace(tmp_txt, LOCKFILE_TXT)

    # A compact orbit-only JSON
    orbits = {
        "description": "Omega mirror orbits for key synchronicities.",
        "examples": [
            {
                "xyz": ex["xyz"],
                "scalar": ex["scalar"],
                "omega_orbit": ex["omega_orbit"],
            }
            for ex in examples
        ],
    }
    tmp_mirror = MIRROR_JSON + ".tmp"
    with open(tmp_mirror, "w") as f:
        json.dump(orbits, f, indent=2)
    os.replace(tmp_mirror, MIRROR_JSON)

    return EXAMPLES_JSON, LOCKFILE_TXT, MIRROR_JSON


if __name__ == "__main__":
    js, txt, mj = run_examples()
    print("Generated mapping:")
    print("  JSON mapping :", js)
    print("  TXT  lock    :", txt)
    print("  JSON orbits  :", mj)
