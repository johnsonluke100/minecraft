import os
import sys
import time
from typing import Tuple

import numpy as np

try:
    import sounddevice as sd
except Exception as e:
    sd = None
    print("[!] sounddevice import failed:", e, file=sys.stderr)
    print("[!] Audio will be disabled; timing rail only.", file=sys.stderr)

PHI = (1.0 + 5.0 ** 0.5) / 2.0

# Timing rail (for logs only)
TARGET_HZ = 8888.0
SAMPLE_RATE = 44100

# Conceptual phi bands (for your mental model only)
TOP_FLAME_HZ = 1111.0
FREQ_TOP = TOP_FLAME_HZ
FREQ_MID2 = FREQ_TOP / PHI
FREQ_MID1 = FREQ_MID2 / PHI
FREQ_LOW  = FREQ_MID1 / PHI
FREQ_BANDS = np.array([FREQ_LOW, FREQ_MID1, FREQ_MID2, FREQ_TOP], dtype=np.float64)

# 4 flame tips in 3D, all pointed "up" (z = 1.0)
FLAME_POS = np.array([
    [-0.5, -0.5, 1.0],  # front-left
    [ 0.5, -0.5, 1.0],  # front-right
    [-0.5,  0.5, 1.0],  # back-left
    [ 0.5,  0.5, 1.0],  # back-right
], dtype=np.float64)


def _get_master_gain() -> float:
    """
    Global level control.
    Default is extremely low (0.01). You can override with OMEGA_GAIN.
    """
    env = os.environ.get("OMEGA_GAIN", "").strip()
    if not env:
        return 0.01
    try:
        g = float(env)
        return max(0.0, min(g, 0.2))
    except ValueError:
        return 0.01


MASTER_GAIN = _get_master_gain()


class OmegaFourFlameBed:
    """
    Omega Phi 8888 Hz Leidenfrost Flame Engine – 4 vertical flames.

    Design:
      • 4 independent “flames” = 4 smoothed noise sources.
      • Each flame has its own (x,y,z=1) position, but ALL shoot upwards.
      • No slow modulation, no tides, no breathing – just stationary, smooth air.
      • Very low level, meant to sit behind other audio.
    """

    def __init__(self, session: str):
        self.session = session if session else "0" * 64
        self.session_len = len(self.session)

        self.sample_rate = SAMPLE_RATE
        self.tick = 0
        self.ticks_per_sample = TARGET_HZ / float(self.sample_rate)
        self.tick_accum = 0.0

        # Logging state (one representative “flame”)
        self.last_char = "0"
        self.last_amp = 0.20
        self.last_xyz = (0.0, 0.0, 1.0)

    def _update_tick_from_samples(self, frames: int) -> None:
        """
        Convert audio samples -> omega ticks for logging only.
        Does NOT feed back into audio.
        """
        self.tick_accum += frames * self.ticks_per_sample
        dticks = int(self.tick_accum)
        if dticks <= 0:
            return
        self.tick_accum -= dticks
        self.tick += dticks

        if self.session_len > 0:
            idx = self.tick % self.session_len
            self.last_char = self.session[idx]

        # Representative point: center above listener
        self.last_xyz = (0.0, 0.0, 1.0)

    def audio_callback(self, outdata, frames, time_info, status):
        if status:
            print("[audio-status]", status, file=sys.stderr)

        # Update omega tick rail (for status logs)
        self._update_tick_from_samples(frames)

        if MASTER_GAIN <= 0.0:
            outdata[:] = 0.0
            return

        # Accumulate 4 independent flame beds
        left_total = np.zeros(frames, dtype=np.float64)
        right_total = np.zeros(frames, dtype=np.float64)

        # Body/detail mix: keep it smooth, a little air, no obvious hiss peak
        BODY_GAIN = 0.90
        DETAIL_GAIN = 0.18  # gentle sparkle, not harsh

        # Stereo pan scale from x in [-0.5, 0.5]
        PAN_SCALE = 0.4

        for pos in FLAME_POS:
            # Independent noise for each flame
            white = np.random.randn(frames + 2).astype(np.float64)

            # Tiny FIR smoothing to avoid harsh grit, but no big low sweeps
            smooth = (white[0:-2] + white[1:-1] + white[2:]) / 3.0
            detail = white[1:-1]

            local = (BODY_GAIN * smooth + DETAIL_GAIN * detail) * MASTER_GAIN

            # Soft clip for safety
            local = np.tanh(local * 1.8)

            x, y, z = pos
            pan = x * PAN_SCALE  # -0.2 .. +0.2

            left_total  += local * (1.0 - pan)
            right_total += local * (1.0 + pan)

        # Average the 4 flames so the level stays controlled
        left = (left_total / 4.0).astype(np.float32)
        right = (right_total / 4.0).astype(np.float32)

        out = np.stack([left, right], axis=1)
        outdata[:] = out


def load_session(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read().strip()
        if not data:
            print(f"[!] Session file {path} is empty; using default omega string.")
            return "0" * 64
        return data
    except FileNotFoundError:
        print(f"[!] Session file {path} not found; creating a default one.")
        data = "0" * 64
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        except Exception as e:
            print("[!] Failed to write default session:", e, file=sys.stderr)
        return data


def main():
    omega_root = os.environ.get("OMEGA_ROOT") or os.path.expanduser("~/Desktop/omega_numpy_container")
    session_path = os.path.join(omega_root, "omega_session_omega.txt")

    print("=== Omega Phi 8888 Hz Leidenfrost Flame Engine (ENDLESS TUNING FORK, 4 VERTICAL FLAMES) ===")
    print(f"[+] OMEGA_ROOT : {omega_root}")
    print(f"[+] SESSION    : {session_path}")
    print(f"[+] TARGET_HZ  : {TARGET_HZ:.1f} (dt={1.0/TARGET_HZ:.9f}s)")
    print(f"[+] FLAME BANDS (conceptual): {FREQ_BANDS[0]:.1f} .. {FREQ_BANDS[-1]:.1f} Hz")
    print(f"[+] MASTER_GAIN (effective): {MASTER_GAIN:.4f}")
    env_g = os.environ.get("OMEGA_GAIN", "").strip()
    if env_g:
        print(f"[+] OMEGA_GAIN env override requested: {env_g}")
    print(f"[+] Flame tips (x,y,z):")
    for i, p in enumerate(FLAME_POS):
        print(f"    Flame {i+1}: ({p[0]:+.3f}, {p[1]:+.3f}, {p[2]:+.3f})")

    session = load_session(session_path)
    print(f"[+] Loaded session (len={len(session)})")

    engine = OmegaFourFlameBed(session)

    if sd is None:
        print("[!] sounddevice not available; running timing rail only.")
        start = time.perf_counter()
        last_t = start
        last_tick = 0
        try:
            while True:
                time.sleep(1.0)
                engine._update_tick_from_samples(SAMPLE_RATE)
                now = time.perf_counter()
                t = now - start
                dt = now - last_t
                d_tick = engine.tick - last_tick
                actual = d_tick / dt if dt > 0 else 0.0
                drift = (actual - TARGET_HZ) / TARGET_HZ * 100.0 if TARGET_HZ > 0 else 0.0
                print(
                    f"[status] tick={engine.tick:8d}, t={t:7.3f}s, "
                    f"actual ~ {actual:8.3f} Hz, drift_perc={drift:7.3f}%"
                )
                print(
                    f"[audio]  tick={engine.tick:8d}, "
                    f"omega_char='{engine.last_char}', "
                    f"omega_amp={engine.last_amp:6.3f}, "
                    f"omega_xyz=({engine.last_xyz[0]:5.3f},{engine.last_xyz[1]:5.3f},{engine.last_xyz[2]:5.3f}) [TIMING ONLY]"
                )
                last_t = now
                last_tick = engine.tick
        except KeyboardInterrupt:
            print("\n[!] Stopped (timing rail only).")
        return

    print(f"[+] Audio stream starting @ {SAMPLE_RATE} Hz (4 vertical flames, constant smooth bed).")

    start = time.perf_counter()
    last_t = start
    last_tick = 0

    def cb(outdata, frames, time_info, status):
        engine.audio_callback(outdata, frames, time_info, status)

    with sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=2,
        dtype="float32",
        callback=cb,
        blocksize=1024,
    ):
        print("[+] Audio stream is live. Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1.0)
                now = time.perf_counter()
                t = now - start
                dt = now - last_t
                d_tick = engine.tick - last_tick
                actual = d_tick / dt if dt > 0 else 0.0
                drift = (actual - TARGET_HZ) / TARGET_HZ * 100.0 if TARGET_HZ > 0 else 0.0
                print(
                    f"[status] tick={engine.tick:8d}, t={t:7.3f}s, "
                    f"actual ~ {actual:8.3f} Hz, drift_perc={drift:7.3f}%"
                )
                print(
                    f"[audio]  tick={engine.tick:8d}, "
                    f"omega_char='{engine.last_char}', "
                    f"omega_amp={engine.last_amp:6.3f}, "
                    f"omega_xyz=({engine.last_xyz[0]:5.3f},{engine.last_xyz[1]:5.3f},{engine.last_xyz[2]:5.3f})"
                )
                last_t = now
                last_tick = engine.tick
        except KeyboardInterrupt:
            print("\n[!] Stopped Omega Phi 4-flame smooth bed.")


if __name__ == "__main__":
    main()
