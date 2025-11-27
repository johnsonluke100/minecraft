package com.lukesky;

import java.awt.Color;

/**
 * Tiny helper to approximate RGB to Minecraft map colors.
 * Not perfect, but good enough for art sky.
 */
public final class MapColorUtil {

    private MapColorUtil() {}

    public static byte rgbToMapColor(int rgb) {
        Color c = new Color(rgb);
        int r = c.getRed();
        int g = c.getGreen();
        int b = c.getBlue();

        // crude luminance bucket
        int lum = (r + g + b) / 3;

        // treat extremes specially
        if (lum < 16) return 0;     // black-ish
        if (lum > 240) return 34;   // white-ish

        // warm vs cool bias
        if (r > g && r > b) {
            // reds / oranges
            if (lum < 64) return 28;
            if (lum < 128) return 29;
            if (lum < 192) return 30;
            return 31;
        } else if (b > r && b > g) {
            // blues / violets
            if (lum < 64) return 40;
            if (lum < 128) return 41;
            if (lum < 192) return 42;
            return 43;
        } else if (g > r && g > b) {
            // greens
            if (lum < 64) return 20;
            if (lum < 128) return 21;
            if (lum < 192) return 22;
            return 23;
        } else {
            // neutral / greys
            if (lum < 64) return 44;
            if (lum < 128) return 45;
            if (lum < 192) return 46;
            return 47;
        }
    }
}
