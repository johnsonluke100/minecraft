package com.lukesky;

import org.bukkit.entity.Player;

/**
 * OmegaMirrorField — scalar → fade.
 *
 * Simple easing:
 *   fade = scalar^2, clamped into [0, 1).
 */
public final class OmegaMirrorField {

    private OmegaMirrorField() {}

    public static double sampleScalar(Player player) {
        return NumpyCoordBridge.encodeFromPlayer(player);
    }

    public static float sampleFade(Player player) {
        double s = sampleScalar(player);
        double eased = s * s;
        if (eased >= 1.0) {
            eased = 0.9999999d;
        }
        return (float) eased;
    }
}
