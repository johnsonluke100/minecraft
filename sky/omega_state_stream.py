#!/usr/bin/env python3
"""
omega_state_stream.py — small helper to peek into the existing
digit-reversal mapping + base-8 omega mirrors created in previous passes.

This does NOT replace or change numpy_coord_mapper.py; it just reads the
files it generated (coord_mapping_examples.json, coord_mirror_orbit.json)
and prints a compact view so you can see the "endless processing loop"
on the command line.

Usage:

  cd ~/Desktop/sky
  python3 omega_state_stream.py
"""

import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_JSON = os.path.join(ROOT, "coord_mapping_examples.json")
MIRROR_JSON = os.path.join(ROOT, "coord_mirror_orbit.json")


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def main():
    examples = load_json(EXAMPLES_JSON)
    mirrors = load_json(MIRROR_JSON)

    print("8XD Omega State Stream")
    print("Root:", ROOT)
    print()

    if not examples:
        print("No coord_mapping_examples.json found.")
        print("Run numpy_coord_mapper.py first to generate lock examples.")
    else:
        print("=== Scalar / Base-8 examples ===")
        for ex in examples.get("examples", []):
            xyz = tuple(ex.get("xyz", [0, 0, 0]))
            scalar = ex.get("scalar", 0.0)
            scalar_base8 = ex.get("scalar_base8", "0.")
            print("xyz = {}  → scalar = {:.12f}  base8 = {}".format(
                xyz, scalar, scalar_base8
            ))
        print()

    if not mirrors:
        print("No coord_mirror_orbit.json found.")
        print("Run numpy_coord_mapper.py first to generate mirror orbits.")
    else:
        print("=== Omega mirror orbits ===")
        for ex in mirrors.get("examples", []):
            xyz = tuple(ex.get("xyz", [0, 0, 0]))
            orbit = ex.get("omega_orbit", [])
            preview = ", ".join("{:.6f}".format(v) for v in orbit[:8])
            print("xyz = {}  → orbit[0..7] = {}".format(xyz, preview))
        print()


if __name__ == "__main__":
    main()
