package com.lukesky;

import org.bukkit.Location;
import org.bukkit.entity.Player;

/**
 * ContinuumMapper
 *
 * Folds classic Minecraft:
 *   - XYZ (blocks)
 *   - yaw / pitch
 *   - vertical position (height / nether depth)
 *
 * into 14 continuum floats between 0 and ~1.
 *
 *  - base10To01: encode a coordinate into 0.xyz... by reversing digits
 *    Example:
 *      0  -> 0.0
 *      10 -> "10" -> "01" -> 0.01
 *      369 -> "369" -> "963" -> 0.963
 */
public final class ContinuumMapper {

    private ContinuumMapper() {}

    private static double base10To01(int coord) {
        coord = Math.abs(coord);
        if (coord == 0) {
            return 0.0;
        }
        String s = Integer.toString(coord);
        StringBuilder sb = new StringBuilder();
        for (int i = s.length() - 1; i >= 0; i--) {
            sb.append(s.charAt(i));
        }
        String reversed = sb.toString();
        String numeric = "0." + reversed;
        double v;
        try {
            v = Double.parseDouble(numeric);
        } catch (NumberFormatException ex) {
            v = 0.999999999999;
        }
        if (v >= 1.0) v = 0.999999999999;
        if (v < 0.0) v = 0.0;
        return v;
    }

    public static double[] map(Player p, double[] previous) {
        if (previous == null || previous.length != 14) {
            previous = new double[14];
        }

        Location loc = p.getLocation();
        int bx = loc.getBlockX();
        int by = loc.getBlockY();
        int bz = loc.getBlockZ();

        double yaw = loc.getYaw();
        double pitch = loc.getPitch();

        double yawNorm = ((yaw + 180.0) / 360.0);
        double pitchNorm = ((pitch + 90.0) / 180.0);

        if (yawNorm < 0.0) yawNorm = 0.0;
        if (yawNorm >= 1.0) yawNorm = 0.999999999999;
        if (pitchNorm < 0.0) pitchNorm = 0.0;
        if (pitchNorm >= 1.0) pitchNorm = 0.999999999999;

        double yHeight = by / 256.0;
        if (yHeight < 0.0) yHeight = 0.0;
        if (yHeight >= 1.0) yHeight = 0.999999999999;

        double xFold = base10To01(bx);
        double yFold = base10To01(by);
        double zFold = base10To01(bz);

        double globeA = xFold;
        double globeB = yFold;
        double globeC = zFold;
        double globeD = (xFold + yFold) / 2.0;
        double globeE = (yFold + zFold) / 2.0;
        double globeF = (xFold + zFold) / 2.0;

        double gExpansion = (xFold + yFold + zFold + yHeight) / 4.0;
        if (gExpansion >= 1.0) gExpansion = 0.999999999999;

        double[] out = new double[14];

        out[0] = xFold;
        out[1] = yFold;
        out[2] = zFold;

        out[3] = yawNorm;
        out[4] = pitchNorm;
        out[5] = (yawNorm + pitchNorm) / 2.0;
        out[6] = yHeight;

        out[7]  = globeA;
        out[8]  = globeB;
        out[9]  = globeC;
        out[10] = globeD;
        out[11] = globeE;
        out[12] = globeF;

        out[13] = gExpansion;

        for (int i = 0; i < 14; i++) {
            if (out[i] < 0.0) out[i] = 0.0;
            if (out[i] >= 1.0) out[i] = 0.999999999999;
        }

        return out;
    }
}
