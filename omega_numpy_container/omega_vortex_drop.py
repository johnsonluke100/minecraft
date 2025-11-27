import math
from dataclasses import dataclass
from typing import Tuple

PHI = (1.0 + 5.0 ** 0.5) / 2.0


@dataclass
class LeidenfrostVortex:
    """
    Leidenfrost-style hourglass / vortex.

    z_norm in [-1, 1] runs from tail (-1) through throat (0) to other tail (+1).
    r_throat is the minimum radius at the middle pinch point.
    r_tail   is the radius at |z_norm| == 1.
    """
    r_throat: float = 0.010     # tight throat
    r_tail: float = 0.060       # fat tails
    power: float = 1.5          # how quickly radius grows away from throat

    def hourglass_radius(self, z_norm: float) -> float:
        """Radius of the 'water column' at this z."""
        z_clamped = max(-1.0, min(1.0, z_norm))
        blend = abs(z_clamped) ** self.power
        return self.r_throat + (self.r_tail - self.r_throat) * blend

    def gain_for_z(self, z_norm: float) -> float:
        """
        Convert position along vortex to gain.

        Center (z=0) ~ 1.0
        Tails (z=±1) ~ ~0.5, smoothly curved.
        """
        z_clamped = max(-1.0, min(1.0, z_norm))
        base = 0.5 + 0.5 * (1.0 - abs(z_clamped))  # simple hourglass profile
        return min(1.0, max(0.0, base ** 1.1))

    def sample_xyz_and_gain(self, z_norm: float) -> Tuple[Tuple[float, float, float], float]:
        """
        Return a pseudo-3D focus vector and gain for a given z_norm.

        x,y are scaled by the hourglass radius.
        z is mapped from [-1,1] into [0,1] for logging aesthetics.
        """
        r = self.hourglass_radius(z_norm)
        gain = self.gain_for_z(z_norm)

        # spiral around the axis so xyz is not static
        angle = math.pi * (z_norm + 1.0)  # 0..2π across -1..+1
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        z = 0.5 * (z_norm + 1.0)          # normalize to 0..1

        max_r = self.r_tail or 1.0
        x_n = 0.5 + 0.5 * (x / max_r)
        y_n = 0.5 + 0.5 * (y / max_r)

        x_n = max(0.0, min(1.0, x_n))
        y_n = max(0.0, min(1.0, y_n))
        z_n = max(0.0, min(1.0, z))

        return (x_n, y_n, z_n), gain

    def debug_hourglass_grid(self) -> None:
        """
        Print a grid similar to the earlier one, but with a real hourglass radius.
        """
        print("z     r0(throat)   r1(hourglass)   gain")
        print("----------------------------------------")
        for z in [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]:
            r0 = self.r_throat
            r1 = self.hourglass_radius(z)
            g = self.gain_for_z(z)
            print(f"{z: .3f}   {r0: .3f}        {r1: .3f}        {g: .3f}")

    def z_from_tick(self, tick: int, target_hz: float, sweep_period_s: float = 8.0) -> float:
        """
        Map a virtual tick index into a vortex z position, sweeping smoothly
        up and down the hourglass over 'sweep_period_s'.
        """
        if target_hz <= 0:
            target_hz = 8888.0
        t = tick / target_hz
        phase = (t / sweep_period_s) * 2.0 * math.pi
        # sinusoidal sweep in z from -1..+1
        return math.sin(phase)


def demo_grid() -> None:
    vortex = LeidenfrostVortex()
    vortex.debug_hourglass_grid()


if __name__ == "__main__":
    demo_grid()
