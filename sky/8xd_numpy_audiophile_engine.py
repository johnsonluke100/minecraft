#!/usr/bin/env python3
"""
8XD Grounded NumPy Audiophile Engine
- Derives ROOT from this file's actual location (no ${SKY_ROOT} mismatch)
- Writes bpm_sync.json into the same folder as this script
- Uses NumPy + sounddevice for audio feature extraction
"""

import os, sys, time, json
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    print("sounddevice is not installed inside .venv_8xd.")
    print("Activate the venv and run: pip install sounddevice numpy")
    sys.exit(1)

# ROOT = actual directory that contains THIS file
ROOT = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(ROOT, "bpm_sync.json")

def clamp01(x):
    x = float(x)
    if x < 0.0:
        return 0.0
    if x >= 1.0:
        return 0.999999999999
    return x

def base10_to_base8_array(values):
    """
    Convert float array (0–1) into a base-8 flavored mapping,
    then fold back into 0–1 range.
    """
    out = []
    for v in values:
        v = clamp01(v)
        o = v * 7.9999999999  # scale to [0, 8)
        out.append(o / 8.0)   # fold back into [0, 1)
    return np.array(out, dtype=np.float64)

def audiophile_smoothing(block):
    """
    Windowed smoothing to create a pleasing, more stable sonic field.
    """
    if len(block) == 0:
        return block
    w = np.hanning(len(block))
    return block * w

def extract_features(block, sr):
    """
    Convert a mono block of audio into:
      - vec14: 14-float continuum vector (0–1, never exactly 1)
      - vec8 : 8-float base hyperface
      - energy, phase_like, superpos, lion: scalar features
    """
    b = audiophile_smoothing(block.astype(np.float64))
    rms = np.sqrt(np.mean(b * b) + 1e-18)
    energy = clamp01(rms * 28.0)

    fft = np.fft.rfft(b)
    mag = np.abs(fft)
    freq = np.fft.rfftfreq(len(b), 1.0 / sr)

    centroid = float(np.sum(freq * mag) / (np.sum(mag) + 1e-18))
    phase_like = clamp01(centroid / (sr / 2.0))

    low = np.sqrt(np.mean(b[: max(1, len(b) // 8)] ** 2) + 1e-18)
    high = np.sqrt(np.mean(b[len(b) // 3 :] ** 2) + 1e-18)
    superpos = clamp01(high / (low + high + 1e-18))

    lion = clamp01((energy + superpos + phase_like) / 3.0)

    vec8 = np.array(
        [energy, phase_like, superpos, lion, 0.1, 0.1, 0.1, 0.1],
        dtype=np.float64,
    )
    vec8 = base10_to_base8_array(vec8)

    # 14-float continuum: forward + mirrored fold
    mirror = vec8[::-1][:6]
    vec14 = np.concatenate([vec8, mirror]).astype(np.float64)

    vec14 = [float(clamp01(v)) for v in vec14]
    vec8_out = [float(clamp01(v)) for v in vec8]

    return vec14, vec8_out, float(energy), float(phase_like), float(superpos), float(lion)

def main():
    if not os.path.isdir(ROOT):
        print("Internal error: ROOT directory missing:", ROOT)
        sys.exit(1)

    sr = 48000
    block = 4096

    print("---------------------------------------------------")
    print("  8XD — GROUNDED NUMPY AUDIOPHILE ENGINE (RUNNING)")
    print("---------------------------------------------------")
    print("Root dir : {}".format(ROOT))
    print("JSON     : {}".format(JSON_PATH))
    print("SampleRate:", sr)
    print("BlockSize :", block)
    print("State     : grounded / focused / present / stable")
    print("---------------------------------------------------")
    sys.stdout.flush()

    try:
        info = sd.query_devices(kind='input')
        max_ch = info.get('max_input_channels', 1)
        if max_ch < 1:
            print("No input channels available on current default device.")
            print("Select a working microphone in macOS System Settings → Sound → Input.")
            sys.exit(1)
    except Exception as e:
        print("Could not query default input device:", e)
        print("Check your microphone settings in macOS.")
        sys.exit(1)

    def callback(indata, frames, time_info, status):
        if status:
            sys.stderr.write(str(status) + "\n")
        try:
            mono = indata[:, 0]
            vec14, vec8, e, p, s, l = extract_features(mono, sr)

            payload = {
                "energy": e,
                "phase": p,
                "superposition": s,
                "lion": l,
                "vec8": vec8,
                "vec14": vec14,
                "timestamp": time.time(),
            }

            tmp = JSON_PATH + ".tmp"
            with open(tmp, "w") as f:
                json.dump(payload, f)
            os.replace(tmp, JSON_PATH)
        except Exception as ex:
            sys.stderr.write("callback error: " + str(ex) + "\n")

    try:
        with sd.InputStream(
            channels=1,
            samplerate=sr,
            blocksize=block,
            callback=callback,
        ):
            while True:
                time.sleep(0.01)
    except Exception as e:
        print("Mic engine error:", e)
        print("Hint: If you see 'Invalid number of channels', choose a mic")
        print("in macOS System Settings → Sound → Input that supports mono.")
        sys.exit(1)

if __name__ == "__main__":
    main()
