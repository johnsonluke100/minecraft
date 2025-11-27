#!/usr/bin/env python3
import json, time, math, os

try:
    import numpy as np
    NUMPY = True
except Exception:
    NUMPY = False

ROOT = os.path.expanduser("~/Desktop/sky")
axes_path = os.path.join(ROOT, "hypercube", "axes14.json")
resolution_path = os.path.join(ROOT, "client", "resolution.json")
frame_path = os.path.join(ROOT, "bpm_sync.json")

phase = 0.0
disc_spin = 0.0

def evolve14():
    global phase
    phase += 0.03
    arr = []
    for i in range(14):
        v = math.sin(phase + i * 0.23) * 0.5 + 0.5
        if v >= 1.0:
            v = 0.999999999999
        if v < 0.0:
            v = 0.0
        arr.append(v)
    if NUMPY:
        return np.array(arr, dtype=float)
    return arr

print("NumPy available:", NUMPY)
print("Starting 14-axis continuum evolution loop (Sequence 6)...")

while True:
    global disc_spin
    disc_spin = (disc_spin + 0.007) % 1.0

    axes = evolve14()
    if NUMPY:
        axes_list = [float(x) for x in axes.tolist()]
    else:
        axes_list = [float(x) for x in axes]

    payload = {
        "ts": time.time(),
        "axes14": axes_list,
        "disc_spin": float(disc_spin),
        "bpm": 0.0,
        "phase": float((phase % (2*math.pi)) / (2*math.pi)),
        "bands": [axes_list[0], axes_list[1], axes_list[2]],
        "resolution": None,
        "note": "Server-side NumPy 14D evolution; mic + true screen ping comes later in the sequence."
    }

    if os.path.exists(resolution_path):
        try:
            with open(resolution_path) as f:
                payload["resolution"] = json.load(f)
        except Exception:
            payload["resolution"] = None

    tmp = frame_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
    os.replace(tmp, frame_path)

    time.sleep(1.0 / 60.0)
