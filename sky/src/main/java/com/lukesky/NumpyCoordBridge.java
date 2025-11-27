package com.lukesky;

import org.bukkit.Location;
import org.bukkit.entity.Player;

/**
 * NumpyCoordBridge — Java mirror of the digit-reversal scalar.
 *
 * Rule:
 *   1) Use |z| (block Z coord) in base-10.
 *   2) Reverse digits as string.
 *   3) Interpret "rev" as "0.rev" in decimal.
 *   4) Clamp into [0, 1) (never exactly 1.0).
 *
 * Examples:
 *
 *   (0,0,1)   → "1"   → "1"   → 0.1
 *   (0,0,10)  → "10"  → "01"  → 0.01
 *   (0,0,369) → "369" → "963" → 0.963
 *   (0,0,248) → "248" → "842" → 0.842
 */
public final class NumpyCoordBridge {

    private NumpyCoordBridge() {}

    public static double encodeScalar(int x, int y, int z) {
        return reversedUnit(z);
    }

    private static double reversedUnit(int n) {
        n = Math.abs(n);
        String s = Integer.toString(n);
        String rev = new StringBuilder(s).reverse().toString();
        String dec = "0." + rev;

        double value;
        try {
            value = Double.parseDouble(dec);
        } catch (NumberFormatException e) {
            value = 0.0;
        }

        if (value < 0.0) {
            value = 0.0;
        }
        if (value >= 1.0) {
            value = 0.999999999999d;
        }
        return value;
    }

    public static double encodeFromPlayer(Player player) {
        if (player == null) {
            return 0.0;
        }
        Location loc = player.getLocation();
        return encodeScalar(loc.getBlockX(), loc.getBlockY(), loc.getBlockZ());
    }
}
