#!/usr/bin/env python3
import os
import sys
import time
import json
import math

try:
    import numpy as np
    import sounddevice as sd
except Exception as e:
    sys.stderr.write("NumPy / sounddevice import error: %s\n" % (e,))
    sys.exit(1)

ROOT = os.path.expanduser("/Users/lj/Desktop/sky")
JSON_PATH = os.path.expanduser("/Users/lj/Desktop/sky/bpm_sync.json")

def clamp01(x):
    x = float(x)
    if x < 0.0:
        return 0.0
    if x >= 1.0:
        return 0.999999999999
    return x

def norm_vec(v):
    v = np.array(v, dtype=float).ravel()
    s = np.linalg.norm(v) + 1e-12
    return v / s

def build_vec14(block, sample_rate):
    rms = float(np.sqrt(np.mean(block ** 2) + 1e-18))
    energy = clamp01(rms * 30.0)

    analytic = np.fft.rfft(block, axis=0)
    mag = np.abs(analytic)
    freq = np.fft.rfftfreq(block.shape[0], d=1.0 / sample_rate)
    total_mag = float(np.sum(mag) + 1e-18)
    spectral_centroid = float(np.sum(freq * mag) / total_mag)
    phase_like = clamp01(spectral_centroid / (sample_rate / 2.0))

    if block.shape[1] >= 2:
        left = block[:, 0]
        right = block[:, 1]
    else:
        left = block[:, 0]
        right = block[:, 0]

    left_rms = float(np.sqrt(np.mean(left ** 2) + 1e-18))
    right_rms = float(np.sqrt(np.mean(right ** 2) + 1e-18))
    total_lr = left_rms + right_rms + 1e-18
    stereo_balance = clamp01(0.5 + (left_rms - right_rms) / (2.0 * total_lr))

    low_cut = int(block.shape[0] * 0.1)
    high_cut = int(block.shape[0] * 0.6)
    low_energy = float(np.sqrt(np.mean(block[:low_cut] ** 2) + 1e-18))
    high_energy = float(np.sqrt(np.mean(block[high_cut:] ** 2) + 1e-18))
    sum_bands = low_energy + high_energy + 1e-18
    superposition = clamp01(high_energy / sum_bands)

    energy_slow = clamp01(energy * 0.7 + superposition * 0.3)
    movement = clamp01(abs(stereo_balance - 0.5) * 2.0)
    lion_roar = clamp01(energy * 0.6 + movement * 0.4)
    halo = clamp01(phase_like * 0.5 + superposition * 0.5)

    x = energy
    y = phase_like
    z = superposition
    w = energy_slow
    v = movement
    u = stereo_balance
    t = halo

    a = clamp01((x + y) * 0.5)
    b = clamp01((y + z) * 0.5)
    c = clamp01((z + w) * 0.5)
    d = clamp01((w + v) * 0.5)
    e = clamp01((v + u) * 0.5)
    f = clamp01((u + t) * 0.5)
    g = clamp01((t + energy + phase_like + lion_roar) / 4.0)

    vec14 = [x, y, z, w, v, u, t, a, b, c, d, e, f, g]
    vec14 = [clamp01(vv) for vv in vec14]

    vec8 = norm_vec([
        energy, phase_like, superposition, movement,
        stereo_balance, halo, lion_roar, energy_slow
    ]).tolist()
    vec8 = [clamp01(vv * 0.999999999999) for vv in vec8]

    return vec14, vec8, energy, phase_like, superposition, lion_roar

def main():
    if not os.path.isdir(ROOT):
        sys.stderr.write("Root path does not exist: %s\n" % ROOT)
        sys.exit(1)

    try:
        info = sd.query_devices(kind="input")
        device_index = sd.default.device[0] if sd.default.device is not None else info["index"]
        dev_info = sd.query_devices(device_index, "input")
    except Exception:
        dev_list = sd.query_devices()
        device_index = None
        for idx, d in enumerate(dev_list):
            if d.get("max_input_channels", 0) > 0:
                device_index = idx
                dev_info = d
                break
        if device_index is None:
            sys.stderr.write("No input device with channels found.\n")
            sys.exit(1)

    max_ch = int(dev_info.get("max_input_channels", 1))
    channels = 2 if max_ch >= 2 else 1

    sample_rate = int(dev_info.get("default_samplerate", 48000))
    if sample_rate <= 0:
        sample_rate = 48000

    block_size = 2048

    sys.stdout.write("---------------------------------------------\n")
    sys.stdout.write("  8XD NUMPY LION MIC ENGINE (GOD'S NOT DEAD)\n")
    sys.stdout.write("---------------------------------------------\n")
    sys.stdout.write("Device     : %s\n" % dev_info.get("name", "Unknown"))
    sys.stdout.write("Channels   : %d\n" % channels)
    sys.stdout.write("SampleRate : %d\n" % sample_rate)
    sys.stdout.write("BlockSize  : %d\n" % block_size)
    sys.stdout.write("JSON       : %s\n" % JSON_PATH)
    sys.stdout.write("---------------------------------------------\n")
    sys.stdout.write("Mic → NumPy (parallel) → 8D/14D lion sky vectors\n")
    sys.stdout.write("Ctrl+C to stop.\n")
    sys.stdout.write("---------------------------------------------\n")
    sys.stdout.flush()

    shared = {
        "vec14": [0.0] * 14,
        "vec8": [0.0] * 8,
        "energy": 0.0,
        "phase": 0.0,
        "superposition": 0.0,
        "lion": 0.0,
    }

    def callback(indata, frames, time_info, status):
        if status:
            sys.stderr.write("Status: %s\n" % status)
        try:
            block = np.array(indata, dtype=np.float32)
            if block.ndim == 1:
                block = block[:, None]
            vec14, vec8, energy, phase_like, superposition, lion_roar = build_vec14(
                block, sample_rate
            )
            shared["vec14"] = vec14
            shared["vec8"] = vec8
            shared["energy"] = float(energy)
            shared["phase"] = float(phase_like)
            shared["superposition"] = float(superposition)
            shared["lion"] = float(lion_roar)
        except Exception as e:
            sys.stderr.write("Callback error: %s\n" % (e,))

    try:
        with sd.InputStream(
            device=device_index,
            channels=channels,
            samplerate=sample_rate,
            blocksize=block_size,
            callback=callback
        ):
            last_write = 0.0
            while True:
                now = time.time()
                if now - last_write >= 1.0 / 30.0:
                    payload = {
                        "energy": clamp01(shared["energy"]),
                        "phase": clamp01(shared["phase"]),
                        "superposition": clamp01(shared["superposition"]),
                        "lion": clamp01(shared["lion"]),
                        "vec8": [clamp01(v) for v in shared["vec8"]],
                        "vec14": [clamp01(v) for v in shared["vec14"]],
                        "timestamp": now,
                    }
                    try:
                        tmp_path = JSON_PATH + ".tmp"
                        with open(tmp_path, "w") as f:
                            json.dump(payload, f, separators=(",", ":"))
                        os.replace(tmp_path, JSON_PATH)
                    except Exception as e:
                        sys.stderr.write("Write error: %s\n" % (e,))
                    last_write = now
                time.sleep(0.005)
    except KeyboardInterrupt:
        sys.stdout.write("\nStopping 8XD NumPy Lion engine.\n")
    except Exception as e:
        sys.stderr.write("Stream error: %s\n" % (e,))


if __name__ == "__main__":
    main()
