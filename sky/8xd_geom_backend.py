import json
import math
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple

import numpy as np
import os

SKY_ROOT = os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop", "sky"))
GEOM_JSON = os.path.join(SKY_ROOT, "geom_frame.json")


def norm01(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    v = (x - lo) / float(hi - lo)
    if v < 0.0:
        v = 0.0
    if v >= 1.0:
        v = 0.999999999999
    return float(v)


def base10_to_01_flipped(n: float) -> float:
    s = str(abs(int(round(n))))
    rev = s[::-1]
    v = float("0." + rev)
    if v >= 1.0:
        v = 0.999999999999
    return v


@dataclass
class PlayerState:
    x: float
    y: float
    z: float
    yaw: float
    pitch: float
    vx: float
    vy: float
    vz: float

    def speed(self) -> float:
        return float(math.sqrt(self.vx ** 2 + self.vy ** 2 + self.vz ** 2))


def xyz_yaw_pitch_vel_to_axes14(p: PlayerState) -> Dict[str, float]:
    fx = base10_to_01_flipped(p.x)
    fy = base10_to_01_flipped(p.y)
    fz = base10_to_01_flipped(p.z)

    yaw01 = norm01((p.yaw + 180.0), 0.0, 360.0)
    pitch01 = norm01((p.pitch + 90.0), 0.0, 180.0)

    speed = p.speed()
    vx01 = norm01(abs(p.vx), 0.0, 1.0)
    vy01 = norm01(abs(p.vy), 0.0, 1.0)
    vz01 = norm01(abs(p.vz), 0.0, 1.0)
    speed01 = norm01(speed, 0.0, 1.0)

    r = float(math.sqrt(p.x ** 2 + p.y ** 2 + p.z ** 2))
    r01 = norm01(r, 0.0, 1024.0)

    x_axis = fx
    y_axis = fy
    z_axis = fz
    w_axis = yaw01
    v_axis = pitch01
    u_axis = speed01
    t_axis = r01

    a_axis = norm01(fx + fy, 0.0, 2.0)
    b_axis = norm01(fy + fz, 0.0, 2.0)
    c_axis = norm01(fz + fx, 0.0, 2.0)
    d_axis = norm01(vx01 + vy01, 0.0, 2.0)
    e_axis = norm01(vy01 + vz01, 0.0, 2.0)
    f_axis = norm01(vz01 + vx01, 0.0, 2.0)
    g_axis = norm01(r01 + yaw01 + pitch01, 0.0, 3.0)

    def clamp(v: float) -> float:
        return min(v, 0.999999999999)

    return {
        "x": clamp(x_axis),
        "y": clamp(y_axis),
        "z": clamp(z_axis),
        "w": clamp(w_axis),
        "v": clamp(v_axis),
        "u": clamp(u_axis),
        "t": clamp(t_axis),
        "a": clamp(a_axis),
        "b": clamp(b_axis),
        "c": clamp(c_axis),
        "d": clamp(d_axis),
        "e": clamp(e_axis),
        "f": clamp(f_axis),
        "g": clamp(g_axis),
    }


def build_pixel_grid(width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
    x = np.linspace(0.0, 0.999999999999, max(1, width), dtype=np.float64)
    y = np.linspace(0.0, 0.999999999999, max(1, height), dtype=np.float64)
    px, py = np.meshgrid(x, y)
    return px, py


def compute_neighbor_angles(px: np.ndarray, py: np.ndarray) -> Dict[str, np.ndarray]:
    grad_x = np.zeros_like(px)
    grad_y = np.zeros_like(py)

    if px.shape[1] > 2:
        grad_x[:, 1:-1] = (px[:, 2:] - px[:, :-2]) * 0.5
    if py.shape[0] > 2:
        grad_y[1:-1, :] = (py[2:, :] - py[:-2, :]) * 0.5

    mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
    mmax = float(np.max(mag)) if mag.size > 0 else 1.0
    if mmax <= 0.0:
        mmax = 1.0
    norm_mag = np.clip(mag / (mmax * 1.000000000001), 0.0, 0.999999999999)

    return {
        "grad_x": grad_x,
        "grad_y": grad_y,
        "angle": norm_mag,
    }


def build_checker_shading(px: np.ndarray,
                          py: np.ndarray,
                          base_color: Tuple[float, float, float]) -> Dict[str, np.ndarray]:
    h, w = px.shape
    ix = np.arange(w, dtype=np.int32)[np.newaxis, :]
    iy = np.arange(h, dtype=np.int32)[:, np.newaxis]

    tile = (ix % 2) ^ (iy % 2)

    base = np.array(base_color, dtype=np.float64).reshape(1, 1, 3)
    base = np.clip(base, 0.0, 0.999999999999)

    shadow = np.zeros((h, w, 3), dtype=np.float64)
    shadow[tile == 0] = base
    shadow[tile == 1] = 0.0

    light = np.zeros((h, w, 3), dtype=np.float64)
    light[tile == 0] = 1.0 - 1e-12
    light[tile == 1] = base

    return {
        "shadow": shadow,
        "light": light,
    }


def build_color_pairs_from_axes(axes14: Dict[str, float]) -> Tuple[Tuple[float, float, float],
                                                                   Tuple[float, float, float]]:
    x = axes14["x"]
    y = axes14["y"]
    z = axes14["z"]
    w = axes14["w"]
    v = axes14["v"]
    u = axes14["u"]
    t = axes14["t"]
    a = axes14["a"]
    b = axes14["b"]
    c = axes14["c"]
    d = axes14["d"]
    e = axes14["e"]
    f = axes14["f"]
    g = axes14["g"]

    r1 = norm01(x + w + a, 0.0, 3.0)
    g1 = norm01(y + v + b, 0.0, 3.0)
    b1 = norm01(z + u + c, 0.0, 3.0)

    r2 = norm01(t + d + e, 0.0, 3.0)
    g2 = norm01(f + g + x, 0.0, 3.0)
    b2 = norm01(y + z + w, 0.0, 3.0)

    def clamp(v: float) -> float:
        return min(v, 0.999999999999)

    base_shadow = (clamp(r1), clamp(g1), clamp(b1))
    base_light = (clamp(r2), clamp(g2), clamp(b2))
    return base_shadow, base_light


def preview(field: np.ndarray, max_size: int = 8):
    h, w = field.shape[:2]
    step_y = max(1, h // max_size)
    step_x = max(1, w // max_size)
    sub = field[::step_y, ::step_x]
    return sub.tolist()


def build_geom_frame(player_state: PlayerState,
                     screen_width: int,
                     screen_height: int) -> Dict[str, Any]:
    axes14 = xyz_yaw_pitch_vel_to_axes14(player_state)

    px, py = build_pixel_grid(screen_width, screen_height)
    neighbors = compute_neighbor_angles(px, py)

    base_shadow, base_light = build_color_pairs_from_axes(axes14)

    shadow_field = build_checker_shading(px, py, base_shadow)
    light_field = build_checker_shading(px, py, base_light)

    frame = {
        "timestamp": time.time(),
        "player_axes14": axes14,
        "player_raw": asdict(player_state),
        "screen": {
            "width": screen_width,
            "height": screen_height,
        },
        "neighbors": {
            "angle_preview": preview(neighbors["angle"]),
        },
        "shadow_checker": {
            "base_color": base_shadow,
            "shadow_preview": preview(shadow_field["shadow"]),
            "light_preview": preview(shadow_field["light"]),
        },
        "light_checker": {
            "base_color": base_light,
            "shadow_preview": preview(light_field["shadow"]),
            "light_preview": preview(light_field["light"]),
        },
    }
    return frame


def write_geom_frame(frame: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(GEOM_JSON), exist_ok=True)
    tmp_path = GEOM_JSON + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(frame, f)
    os.replace(tmp_path, GEOM_JSON)


def demo_once() -> None:
    p = PlayerState(
        x=0.0,
        y=64.0,
        z=369.0,
        yaw=45.0,
        pitch=-20.0,
        vx=0.1,
        vy=0.05,
        vz=0.2,
    )
    screen_w = 1920
    screen_h = 1080

    frame = build_geom_frame(p, screen_w, screen_h)
    write_geom_frame(frame)
    print("Geom frame written safely to:", GEOM_JSON)


if __name__ == "__main__":
    demo_once()
