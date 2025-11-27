#!/usr/bin/env python3
import json, time, os

ROOT = os.path.expanduser("~/Desktop/sky")
out_dir = os.path.join(ROOT, "client")
out = os.path.join(out_dir, "resolution.json")
os.makedirs(out_dir, exist_ok=True)

payload = {
    "ts": time.time(),
    "width": 1920,
    "height": 1080,
    "quadrant_width": 1920 // 4,
    "quadrant_height": 1080 // 4,
    "note": "Stubbed client resolution. Real 2-way ping will replace this."
}

tmp = out + ".tmp"
with open(tmp, "w") as f:
    json.dump(payload, f)
os.replace(tmp, out)

print("Client resolution stub written:", out)
