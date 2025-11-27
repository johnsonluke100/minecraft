package com.lukesky;

import java.util.HashMap;
import java.util.Map;

/**
 * HypercubeRegistry
 *
 * 14-axis float model per player:
 *   x, y, z,
 *   w, v, u, t,
 *   a, b, c, d, e, f,
 *   g
 *
 * Each value is clamped into [0, 0.999999999999].
 * 0 = undefined fractal / placeholder.
 * 1 is never exactly reached, only approached.
 */
public final class HypercubeRegistry {

    private static final Map<String, double[]> STATE = new HashMap<String, double[]>();

    private HypercubeRegistry() {}

    public static void initPlayer(String uuid) {
        STATE.put(uuid, new double[]{
                0,0,0, 0,0,0,0,
                0,0,0,0,0,0,
                0
        });
    }

    public static boolean hasPlayer(String uuid) {
        return STATE.containsKey(uuid);
    }

    public static double[] getAxes(String uuid) {
        return STATE.get(uuid);
    }

    public static void setAxes(String uuid, double[] values) {
        if (values == null || values.length != 14) return;
        double[] clamped = new double[14];
        for (int i = 0; i < 14; i++) {
            double v = values[i];
            if (v < 0.0) v = 0.0;
            if (v >= 1.0) v = 0.999999999999;
            clamped[i] = v;
        }
        STATE.put(uuid, clamped);
    }

    public static void updateAxis(String uuid, int index, double value) {
        if (index < 0 || index >= 14) return;
        double[] cur = STATE.get(uuid);
        if (cur == null) {
            initPlayer(uuid);
            cur = STATE.get(uuid);
        }
        if (value < 0.0) value = 0.0;
        if (value >= 1.0) value = 0.999999999999;
        cur[index] = value;
    }
}
