#!/usr/bin/env python3
"""
8XD Omega Base-8 Harmonics — Mirror Edition

Takes 14-float continuum (a..g + g..a) and collapses into
an 8-element omega vector.

This is where the "sound cube" spins:
  • Channels 0..6: pairwise average of each mirror pair.
  • Channel 7    : overall omega energy (max of forward/back).

You can feed this ω8 vector into your mic engine and then into
the DJ-side 8XD audio driver.
"""

import os
from typing import List

try:
    import numpy as np
except ImportError:
    np = None


ROOT = os.path.dirname(os.path.abspath(__file__))


def clamp_unit_array(arr):
    if np is None:
        return [max(0.0, min(0.999999999999, float(x))) for x in arr]
    return np.clip(arr.astype(float), 0.0, 0.999999999999)


def continuum14_to_omega8(vec14: List[float]):
    """
    Collapse 14 floats into an 8-element ω vector.

    vec14 = [a, b, c, d, e, f, g, g', f', e', d', c', b', a']
    """
    if len(vec14) != 14:
        raise ValueError("Expected 14-element continuum, got {}".format(len(vec14)))

    if np is None:
        f = [float(v) for v in vec14[:7]]
        b = [float(v) for v in vec14[7:]]
        channels = [
            (f[0] + b[0]) / 2.0,
            (f[1] + b[1]) / 2.0,
            (f[2] + b[2]) / 2.0,
            (f[3] + b[3]) / 2.0,
            (f[4] + b[4]) / 2.0,
            (f[5] + b[5]) / 2.0,
            (f[6] + b[6]) / 2.0,
            (max(f) + max(b)) / 2.0,
        ]
        return clamp_unit_array(channels)

    v = np.array(vec14, dtype=float)
    f = v[:7]
    b = v[7:]

    channels = np.zeros(8, dtype=float)
    channels[:7] = (f + b) / 2.0
    channels[7] = (np.max(f) + np.max(b)) / 2.0

    return clamp_unit_array(channels)


if __name__ == "__main__":
    test = [i / 20.0 for i in range(14)]
    omega = continuum14_to_omega8(test)
    print("ROOT:", ROOT)
    print("vec14:", ", ".join("{:.3f}".format(v) for v in test))
    print("ω8  :", ", ".join("{:.3f}".format(v) for v in omega))
