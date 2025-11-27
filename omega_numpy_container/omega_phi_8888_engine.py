import os
import sys
import time
import math
from typing import Tuple

import numpy as np
from omega_vortex_drop import LeidenfrostVortex, PHI

OMEGA_ROOT = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(OMEGA_ROOT, "omega_session_omega.txt")

TARGET_HZ = 8888.0
DT = 1.0 / TARGET_HZ

SAMPLE_RATE = 44100
CONTROL_HZ = 1000.0  # control loop for parameter updates

# Try to get sounddevice
try:
    import sounddevice as sd  # type: ignore
    HAS_SD = True
    SD_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    HAS_SD = False
    SD_IMPORT_ERROR = e


def load_session(path: str) -> str:
    if not os.path.exists(path):
        # Fallback short sequence if session file is missing
        return "T00000F26000C04220S02040E06660L06660L16240L26620L32020D02660D16660D26660D34060D"
    with open(path, "r", encoding="utf-8") as f:
        data = f.read().strip()
    return data or "0" * 64


def char_to_base_amp(ch: str) -> float:
    """
    Base amplitude before vortex gain.
    """
    lut = {
        "0": 1.00,
        "F": 0.95,
        "E": 0.90,
        "D": 0.85,
        "C": 0.80,
        "B": 0.75,
        "A": 0.70,
        "9": 0.60,
        "8": 0.55,
        "7": 0.50,
        "6": 0.45,
        "5": 0.35,
        "4": 0.25,
        "3": 0.22,
        "2": 0.28,
        "1": 0.20,
        "T": 0.40,
        "S": 0.35,
        "L": 0.00,
        ".": 0.00,
        ":": 0.15,
        "m": 0.00,
    }
    return lut.get(ch, 0.18)


def char_to_octave_weights(ch: str) -> np.ndarray:
    """
    Map omega_char → weights for the 4 Phi octaves (flame tips).

    Index 0: lowest octave (deep embers, bottom of flame)
           3: highest octave (sharp tip, hottest)
    """
    # Deep-focused
    if ch in "12TS":
        w = np.array([0.55, 0.30, 0.10, 0.05], dtype=np.float64)
    # Mid-band
    elif ch in "34567a":
        w = np.array([0.25, 0.40, 0.25, 0.10], dtype=np.float64)
    # Bright / piercing
    elif ch in "089FEDC":
        w = np.array([0.10, 0.25, 0.30, 0.35], dtype=np.float64)
    # Silence / near-silence
    elif ch in "L.m":
        w = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    else:
        w = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float64)

    s = float(np.sum(w))
    if s <= 0.0:
        return w
    return w / s


def build_phi_octave_freqs(top_hz: float) -> np.ndarray:
    """
    Build four Phi-based octaves, clamped into 88–8888 Hz.
    """
    exponents = [3.0, 2.0, 1.0, 0.0]
    raw = [top_hz / (PHI ** e) for e in exponents]
    arr = np.array(raw, dtype=np.float64)
    arr = np.clip(arr, 88.0, 8888.0)
    return arr


class OmegaAudioEngine:
    """
    4-oscillator Phi engine with 4 flame tips in stereo.

    - Each octave is a "flame tip".
    - Tips are placed at different stereo pans (speaker quadrants).
    - Amplitudes are smoothed per block to avoid static hiss.
    """

    def __init__(self, sample_rate: int, top_hz: float):
        self.sample_rate = sample_rate
        self.freqs = build_phi_octave_freqs(top_hz)

        self._amps = np.zeros(4, dtype=np.float64)
        self._amps_target = np.zeros(4, dtype=np.float64)
        self._phases = np.zeros(4, dtype=np.float64)

        # 4 flame tips across stereo field: farL, midL, midR, farR
        self._pan = np.array([-0.75, -0.25, 0.25, 0.75], dtype=np.float64)
        self._panL = np.sqrt(0.5 * (1.0 - self._pan))  # constant-power panning
        self._panR = np.sqrt(0.5 * (1.0 + self._pan))

        self._lock = None  # created after numpy import
        self._global_gain = 0.8
        self._smoothing = 0.08  # 0..1, per audio block

        import threading  # local import to avoid confusion
        self._lock = threading.Lock()
        self._stream = None
        self._running = False

        if HAS_SD:
            self._start_stream()
        else:  # pragma: no cover
            print("[!] sounddevice is NOT available. Audio will be TIMING ONLY.", file=sys.stderr)
            if SD_IMPORT_ERROR is not None:
                print(f"[!] Import error was: {SD_IMPORT_ERROR}", file=sys.stderr)

    def _start_stream(self) -> None:
        def callback(outdata, frames, time_info, status):  # type: ignore[override]
            if status:  # pragma: no cover
                print(f"[sd] status: {status}", file=sys.stderr)

            t = np.arange(frames, dtype=np.float64)

            with self._lock:
                freqs = self.freqs.copy()
                amps = self._amps.copy()
                amps_target = self._amps_target.copy()
                phases = self._phases.copy()
                panL = self._panL.copy()
                panR = self._panR.copy()

            # Smooth amplitudes toward target (single-pole lowpass)
            alpha = self._smoothing
            amps = amps + alpha * (amps_target - amps)

            phase_inc = 2.0 * math.pi * freqs / self.sample_rate
            phases_mat = phases[:, None] + phase_inc[:, None] * t[None, :]

            sines = np.sin(phases_mat)
            osc = amps[:, None] * sines  # (4, frames)

            left = np.sum(osc * panL[:, None], axis=0)
            right = np.sum(osc * panR[:, None], axis=0)

            # Update phases (advance by frames)
            phases = phases + phase_inc * frames
            phases = np.mod(phases, 2.0 * math.pi)

            with self._lock:
                self._amps[:] = amps
                self._phases[:] = phases

            # Soft limiter / safety
            left = np.tanh(self._global_gain * left)
            right = np.tanh(self._global_gain * right)

            outdata[:, 0] = left.astype(np.float32)
            outdata[:, 1] = right.astype(np.float32)

        self._stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=2,  # stereo: 4 flame tips folded into L/R
            dtype="float32",
            callback=callback,
            blocksize=0,
        )
        self._stream.start()
        self._running = True
        print(f"[+] Audio stream started @ {self.sample_rate} Hz with 4 Phi octaves (stereo flame).")

    def update_from_char(self, omega_char: str, total_amp: float, xyz: Tuple[float, float, float]) -> None:
        """
        Called by the timing rail: update target amplitudes for the 4 tips.
        xyz is the vortex position; we use z to bias bright vs deep tips.
        """
        total_amp = max(0.0, min(0.95, total_amp))
        weights = char_to_octave_weights(omega_char)

        base = total_amp * weights

        z = max(0.0, min(1.0, xyz[2]))
        # z=0   → more deep, less bright
        # z=1   → more bright, less deep
        shape = np.array([
            1.0 - 0.3 * z,    # octave 0 (deep)
            0.9 - 0.1 * z,    # octave 1
            0.7 + 0.1 * z,    # octave 2
            0.5 + 0.5 * z,    # octave 3 (tip)
        ], dtype=np.float64)
        shape = np.clip(shape, 0.0, 1.5)

        amps_target = base * shape

        with self._lock:
            self._amps_target[:] = amps_target

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
        self._running = False


def main() -> None:
    print("=== Omega Phi 8888 Hz Leidenfrost Flame Engine (ENDLESS TUNING FORK) ===")
    print(f"[+] OMEGA_ROOT : {OMEGA_ROOT}")
    print(f"[+] SESSION    : {SESSION_FILE}")
    print(f"[+] TARGET_HZ  : {TARGET_HZ} (dt={DT:.9f}s)")

    session = load_session(SESSION_FILE)
    print(f"[+] Loaded session (len={len(session)})")

    vortex = LeidenfrostVortex()
    audio = OmegaAudioEngine(SAMPLE_RATE, TARGET_HZ)

    if not HAS_SD:
        print("[!] Audio = TIMING ONLY (no sounddevice).")

    t0 = time.perf_counter()
    next_report_t = 1.0  # first status at ~1s

    try:
        while True:
            loop_start = time.perf_counter()
            elapsed_s = loop_start - t0
            if elapsed_s <= 0:
                elapsed_s = 1e-9

            # Virtual 8888 Hz tick based on REAL time:
            tick_virtual = int(elapsed_s * TARGET_HZ)

            ch = session[tick_virtual % len(session)]
            base_amp = char_to_base_amp(ch)

            z_norm = vortex.z_from_tick(tick_virtual, TARGET_HZ, sweep_period_s=8.0)
            xyz, gain = vortex.sample_xyz_and_gain(z_norm)
            total_amp = base_amp * gain

            if HAS_SD:
                audio.update_from_char(ch, total_amp, xyz)

            if elapsed_s >= next_report_t:
                actual_hz = tick_virtual / elapsed_s
                drift = ((actual_hz - TARGET_HZ) / TARGET_HZ) * 100.0
                sec = int(round(elapsed_s))

                print(
                    f"[status] tick={tick_virtual:8d}, t={sec:4d}.000s, "
                    f"actual ~ {actual_hz:8.3f} Hz, drift_perc={drift:7.3f}%"
                )
                tag = "" if HAS_SD else " [TIMING ONLY]"
                print(
                    f"[audio]  tick={tick_virtual:8d}, omega_char='{ch}', "
                    f"omega_amp={total_amp:6.3f}, "
                    f"omega_xyz=({xyz[0]:0.3f},{xyz[1]:0.3f},{xyz[2]:0.3f}){tag}"
                )

                next_report_t += 1.0

            # Control loop pacing (~1 kHz)
            control_dt = 1.0 / CONTROL_HZ
            elapsed_loop = time.perf_counter() - loop_start
            to_sleep = control_dt - elapsed_loop
            if to_sleep > 0:
                time.sleep(to_sleep)

    except KeyboardInterrupt:
        print("\n[!] KeyboardInterrupt — stopping Omega engine...")
    finally:
        audio.stop()
        print("[+] Omega engine shut down cleanly.")


if __name__ == "__main__":
    main()
