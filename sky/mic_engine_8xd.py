#!/usr/bin/env python3
# mic_engine_8xd.py
import json
import os
import time
import math
from threading import Lock

import numpy as np
import sounddevice as sd

ROOT = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(ROOT, "bpm_sync.json")

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

_state_lock = Lock()
_state = {
    "time": 0.0,
    "z": 0.0,
    "y": 0.0,
    "x": 0.0,
    "w": 0.0,
    "v": 0.0,
    "u": 0.0,
    "t": 0.0,
    "a": 0.0,
    "b": 0.0,
    "c": 0.0,
    "d": 0.0,
    "e": 0.0,
    "f": 0.0,
    "g": 0.0,
}

def clamp01(x: float) -> float:
    if math.isnan(x) or math.isinf(x):
        return 0.0
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 0.9999999999
    return float(x)

def safe_norm(v: np.ndarray) -> float:
    v = np.asarray(v, dtype=float)
    if v.size == 0:
        return 0.0
    s = float(np.sum(v * v))
    if s <= 0.0:
        return 0.0
    return float(math.sqrt(s))

def fft_bands(mono: np.ndarray, sr: int, n_bands: int = 7):
    n = len(mono)
    if n <= 0:
        return [0.0] * n_bands

    window = np.hanning(n)
    spec = np.fft.rfft(mono * window)
    mag = np.abs(spec)

    freqs = np.fft.rfftfreq(n, d=1.0 / sr)

    bands = np.zeros(n_bands, dtype=float)

    min_f = 20.0
    max_f = 20000.0
    log_min = math.log10(min_f)
    log_max = math.log10(max_f)
    edges = np.logspace(log_min, log_max, num=n_bands + 1)

    for bi in range(n_bands):
        f_lo = edges[bi]
        f_hi = edges[bi + 1]
        idx = np.where((freqs >= f_lo) & (freqs < f_hi))[0]
        if idx.size > 0:
            bands[bi] = float(np.mean(mag[idx]))
        else:
            bands[bi] = 0.0

    total = float(np.sum(bands))
    if total > 0.0:
        bands = bands / total
    return [clamp01(float(b)) for b in bands]

def compute_14_float_from_audio(block: np.ndarray, sr: int):
    if block.ndim == 2:
        mono = block.mean(axis=1)
    else:
        mono = block

    mono = mono.astype(np.float64)
    if mono.size == 0:
        bands = [0.0] * 7
        rms = 0.0
    else:
        mono = mono / (np.max(np.abs(mono)) + 1e-9)
        bands = fft_bands(mono, sr, 7)
        rms = safe_norm(mono) / math.sqrt(float(mono.size))
        rms = clamp01(rms)

    a = bands[0]
    b = bands[1]
    c = bands[2]
    d = bands[3]
    e = bands[4]
    f = bands[5]
    g = bands[6]

    if rms > g:
        g_val = clamp01(rms)
        t_val = 0.0
    else:
        g_val = clamp01(g)
        t_val = clamp01(1.0 - g_val)

    z = 0.0
    y = 0.0
    x = 0.0
    w = 0.0
    v = 0.0
    u = 0.0

    return {
        "z": z,
        "y": y,
        "x": x,
        "w": w,
        "v": v,
        "u": u,
        "t": t_val,
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "e": e,
        "f": f,
        "g": g_val,
    }

def write_state():
    with _state_lock:
        data = dict(_state)
    tmp = JSON_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    os.replace(tmp, JSON_PATH)

def audio_callback(indata, frames, time_info, status):
    global _state
    if status:
        pass
    try:
        floats = compute_14_float_from_audio(indata, SAMPLE_RATE)
        now = time.time()
        with _state_lock:
            _state["time"] = float(now)
            for k, v in floats.items():
                _state[k] = float(v)
        write_state()
    except Exception:
        pass

def main():
    if not os.path.exists(JSON_PATH):
        write_state()

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype="float32",
        callback=audio_callback,
    )

    with stream:
        while True:
            time.sleep(0.1)

if __name__ == "__main__":
    main()
