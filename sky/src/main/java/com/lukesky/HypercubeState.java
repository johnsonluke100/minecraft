package com.lukesky;

import org.bukkit.Location;
import org.bukkit.entity.Player;

/**
 * HypercubeState
 *
 * 14 float-like coordinates in [0, 1) representing:
 *   a b c d e f g z y x w v u t
 *
 * Conceptually:
 *   - Positive / negative expansion
 *   - 6 face-lean directions
 *   - 8-corner hypercube style potential
 *
 * Implementation is deliberately simple and safe:
 *   - All values clamped into [0, 1)
 *   - Derived deterministically from player XYZ + yaw + pitch
 *   - The deeper NumPy continuum lives outside Java, in your Python engine
 */
public class HypercubeState {

    // 14 axes, each in [0, 1)
    public double a, b, c, d, e, f, g, z, y, x, w, v, u, t;

    public HypercubeState() {
        zero();
    }

    public void zero() {
        a = b = c = d = e = f = g = z = y = x = w = v = u = t = 0.0;
    }

    /**
     * Update this hypercube state from a given player.
     * This is a placeholder mapping that keeps everything finite and safe,
     * ready to be reinterpreted by NumPy in arbitrarily high dimensions.
     */
    public void updateFromPlayer(Player player) {
        if (player == null) {
            zero();
            return;
        }

        Location loc = player.getLocation();

        double px = loc.getX();
        double py = loc.getY();
        double pz = loc.getZ();

        double yaw = loc.getYaw();   // -180..180
        double pitch = loc.getPitch(); // -90..90

        // Normalize XYZ via tanh-ish squashing: values far from 0 converge toward ±1
        double nx = squash(px * 0.01);
        double ny = squash(py * 0.01);
        double nz = squash(pz * 0.01);

        // Map yaw/pitch into [0, 1)
        double nyaw = ((yaw + 180.0) / 360.0);
        double npitch = ((pitch + 90.0) / 180.0);

        nyaw = clamp01(nyaw);
        npitch = clamp01(npitch);

        // 14 floats:
        // faces / poles
        a = clamp01(0.5 + nx * 0.5);     // east lean-ish
        c = clamp01(0.5 - nx * 0.5);     // west
        b = clamp01(0.5 + nz * 0.5);     // north
        d = clamp01(0.5 - nz * 0.5);     // south
        e = clamp01(0.5 + ny * 0.5);     // up
        f = clamp01(0.5 - ny * 0.5);     // down

        // expansion / contraction proxies
        g = clamp01((Math.abs(nx) + Math.abs(ny) + Math.abs(nz)) / 3.0);   // expansion
        t = clamp01(1.0 - g);                                              // contraction

        // orientation + velocity-like proxies
        w = nyaw;
        v = npitch;

        // simple pairings for remaining axes
        u = clamp01((nx + nz + 1.0) * 0.5);
        x = clamp01((nx + 1.0) * 0.5);
        y = clamp01((ny + 1.0) * 0.5);
        z = clamp01((nz + 1.0) * 0.5);
    }

    private double squash(double v) {
        // safe tanh-like squashing using v / (1 + |v|)
        double denom = 1.0 + Math.abs(v);
        double r = v / denom;
        return r; // in (-1, 1)
    }

    private double clamp01(double v) {
        if (v < 0.0) return 0.0;
        if (v >= 1.0) return Math.nextAfter(1.0, 0.0);
        return v;
    }
}
