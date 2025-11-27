#!/bin/bash
set -e

echo "---------------------------------------------"
echo "  MINECRAFT 8XD — NUMPY 8XD MIC ENGINE"
echo "---------------------------------------------"

# Resolve SKY_ROOT as the folder where this script lives
SKY_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SKY_ROOT/.venv_8xd"
JSON_FILE="$SKY_ROOT/bpm_sync.json"

echo "Root : $SKY_ROOT"
echo "Venv : $VENV_DIR"
echo "JSON : $JSON_FILE"
echo

if [ ! -d "$VENV_DIR" ]; then
  echo "8XD venv missing. Creating now…"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install numpy sounddevice
fi

echo "Launching NumPy 8XD mic engine…"
"$VENV_DIR/bin/python" - << 'PYEOF'
import json
import math
import time
import sys

import numpy as np

try:
    import sounddevice as sd
except Exception as e:
    print("sounddevice import failed inside venv:", e)
    sys.exit(1)

SKY_ROOT = r"/Users/lj/Desktop/sky"
# We'll patch this string at runtime from bash; see below.
JSON_FILE = None

def init_paths():
    global SKY_ROOT, JSON_FILE
    # SKY_ROOT gets injected by the launcher; if still placeholder, fallback.
    if SKY_ROOT == "REPLACE_AT_RUNTIME":
        import os
        SKY_ROOT = os.getcwd()
    JSON_FILE = SKY_ROOT.rstrip("/") + "/bpm_sync.json"

def get_input_channels():
    """Pick a valid input channel count for the default device."""
    try:
        dev = sd.default.device[0]  # input device index
        info = sd.query_devices(dev)
        max_in = info.get("max_input_channels", 1)
        if max_in <= 0:
            print("No valid input channels on default device.")
            return None
        # Prefer mono (1) to keep math simple, but fall back to 2 if needed.
        return 1 if max_in >= 1 else max_in
    except Exception as e:
        print("Failed to query input device:", e)
        return None

def norm01(x, lo, hi):
    """Clamp + map into [0,1) (but never exactly 1.0)."""
    if hi <= lo:
        return 0.0
    v = (x - lo) / float(hi - lo)
    if v < 0.0:
        v = 0.0
    if v >= 1.0:
        v = 0.999999999999
    return float(v)

def base10_to_01_flipped(n):
    """
    Convert a non-negative integer into 0.x format by reversing digits.
    Example:
      1   -> 0.1
      10  -> 0.01
      369 -> 0.963
    Then clamp to [0,1).
    """
    s = str(abs(int(n)))
    rev = s[::-1]
    v = float("0." + rev)
    if v >= 1.0:
        v = 0.999999999999
    return v

def compute_8xd_vectors(audio, samplerate):
    """
    Take raw audio buffer and compute:
      - 14D continuum axes (x,y,z,w,v,u,t,a,b,c,d,e,f,g)
      - 8XD superposition vector (8 floats)
      - basic bands + rms
    """
    # Convert to mono ndarray (float64)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float64)

    # Basic RMS + peak
    if audio.size == 0:
        rms = 0.0
        peak = 0.0
    else:
        rms = float(np.sqrt(np.mean(audio ** 2)))
        peak = float(np.max(np.abs(audio)))

    # Short FFT
    if audio.size < 32:
        fft_mag = np.zeros(16, dtype=np.float64)
    else:
        fft = np.fft.rfft(audio * np.hanning(audio.size))
        fft_mag = np.abs(fft)

    # Frequency bins
    if fft_mag.size < 8:
        fft_mag = np.pad(fft_mag, (0, 8 - fft_mag.size))
    freqs = np.fft.rfftfreq(audio.size, 1.0 / samplerate) if audio.size > 0 else np.arange(fft_mag.size)

    # Four broad bands: low, low-mid, high-mid, air
    bands = []
    ranges = [
        (20, 200),     # low
        (200, 800),    # low-mid
        (800, 4000),   # high-mid
        (4000, 20000)  # air
    ]
    for lo, hi in ranges:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            bands.append(0.0)
        else:
            val = float(np.mean(fft_mag[mask]))
            bands.append(val)

    # Normalize bands into [0,1)
    if bands:
        max_band = max(bands) or 1.0
    else:
        max_band = 1.0
    bands01 = [norm01(b, 0.0, max_band * 1.5) for b in bands]

    # Rough BPM estimate proxy from low-mid band energy
    # We don't solve full BPM; we produce a stable 0–1 value that "feels" like intensity.
    bpm_like = norm01(bands01[1], 0.0, 1.0)

    # Phase proxy (using dominant bin)
    if fft_mag.size > 0:
        idx = int(np.argmax(fft_mag))
        phase_proxy = norm01(idx, 0, fft_mag.size)
    else:
        phase_proxy = 0.0

    # Now construct the 14D axes using audio features
    # Names: x,y,z,w,v,u,t,a,b,c,d,e,f,g
    # We'll use combinations of rms, peak, bands, bpm_like, phase_proxy
    x = norm01(rms, 0.0, 0.25)                      # loudness baseline
    y = norm01(peak, 0.0, 0.8)                      # transients
    z = bands01[0]                                  # low
    w = bands01[1]                                  # low-mid
    v = bands01[2]                                  # high-mid
    u = bands01[3]                                  # air
    t = bpm_like                                    # "tempo" energy
    a = norm01(rms * bands01[0], 0.0, 0.3)
    b = norm01(rms * bands01[1], 0.0, 0.3)
    c = norm01(rms * bands01[2], 0.0, 0.3)
    d = norm01(rms * bands01[3], 0.0, 0.3)
    e = norm01(phase_proxy, 0.0, 1.0)
    f = norm01((bands01[0] + bands01[3]) * 0.5, 0.0, 1.0)
    g = norm01((bands01[1] + bands01[2]) * 0.5, 0.0, 1.0)

    axes14 = [x,y,z,w,v,u,t,a,b,c,d,e,f,g]

    # 8XD vector: base-8 themed mapping from axes14
    # We fold the 14D state into 8 positions
    super8 = [
        norm01(x + z, 0.0, 2.0),
        norm01(y + w, 0.0, 2.0),
        norm01(v + u, 0.0, 2.0),
        norm01(t + a, 0.0, 2.0),
        norm01(b + c, 0.0, 2.0),
        norm01(d + e, 0.0, 2.0),
        norm01(f + g, 0.0, 2.0),
        norm01(rms + peak, 0.0, 1.5),
    ]

    # Guarantee nothing is exactly 1.0
    super8 = [min(v, 0.999999999999) for v in super8]

    return {
        "axes14": axes14,
        "super8": super8,
        "bands01": bands01,
        "rms": rms,
        "peak": peak,
        "bpm_like": bpm_like,
        "phase": phase_proxy,
    }

def write_state_to_json(state):
    payload = {
        "source": "8xd_mic_engine",
        "version": 1,
        "timestamp": time.time(),
        "axes14": state["axes14"],
        "super8": state["super8"],
        "bands01": state["bands01"],
        "rms": state["rms"],
        "peak": state["peak"],
        "bpm_like": state["bpm_like"],
        "phase": state["phase"],
    }
    try:
        with open(JSON_FILE, "w") as f:
            json.dump(payload, f)
    except Exception as e:
        print("Failed to write JSON:", e)

def audio_callback(indata, frames, time_info, status):
    if status:
        # We log but do not crash
        print("Audio status:", status, file=sys.stderr)
    try:
        state = compute_8xd_vectors(indata, sd.default.samplerate)
        write_state_to_json(state)
    except Exception as e:
        print("Error in callback:", e, file=sys.stderr)

def main():
    init_paths()
    ch = get_input_channels()
    if ch is None:
        print("Cannot start mic engine: no valid input channels.")
        return

    sd.default.channels = ch
    if sd.default.samplerate is None:
        sd.default.samplerate = 48000

    print("---------------------------------------------")
    print("8XD NumPy mic engine running.")
    print("Mic → 14D axes → 8XD vector →", JSON_FILE)
    print("Press Ctrl+C to stop.")
    print("---------------------------------------------")

    try:
        with sd.InputStream(channels=ch, callback=audio_callback):
            while True:
                time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nMic engine stopped by user.")
    except Exception as e:
        print("Fatal audio error:", e)

if __name__ == "__main__":
    main()
PYEOF
