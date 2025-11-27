package com.lukesky;

import java.awt.Color;

/**
 * MapColorProfile
 *
 * Represents a 4-checker pattern:
 *   [ light, lightHighlight, shadow, shadowDeep ]
 *
 * We do not directly draw maps yet — this is a pure
 * color / geometry description that will be wired into
 * armor-stand map shells in later sequences.
 */
public final class MapColorProfile {

    private final String id;
    private final Color lightColor;
    private final Color lightHighlight;
    private final Color shadowColor;
    private final Color shadowDeep;

    public MapColorProfile(String id,
                           Color lightColor,
                           Color lightHighlight,
                           Color shadowColor,
                           Color shadowDeep) {
        this.id = id;
        this.lightColor = lightColor;
        this.lightHighlight = lightHighlight;
        this.shadowColor = shadowColor;
        this.shadowDeep = shadowDeep;
    }

    public String getId() {
        return id;
    }

    public Color getLightColor() {
        return lightColor;
    }

    public Color getLightHighlight() {
        return lightHighlight;
    }

    public Color getShadowColor() {
        return shadowColor;
    }

    public Color getShadowDeep() {
        return shadowDeep;
    }

    public Color blendLight(double t) {
        if (t < 0.0) t = 0.0;
        if (t > 1.0) t = 1.0;
        return lerp(lightColor, lightHighlight, t);
    }

    public Color blendShadow(double t) {
        if (t < 0.0) t = 0.0;
        if (t > 1.0) t = 1.0;
        return lerp(shadowColor, shadowDeep, t);
    }

    private static Color lerp(Color a, Color b, double t) {
        int r = (int) Math.round(a.getRed()   + (b.getRed()   - a.getRed())   * t);
        int g = (int) Math.round(a.getGreen() + (b.getGreen() - a.getGreen()) * t);
        int bl = (int) Math.round(a.getBlue() + (b.getBlue()  - a.getBlue())  * t);

        if (r < 0) r = 0;
        if (r > 255) r = 255;
        if (g < 0) g = 0;
        if (g > 255) g = 255;
        if (bl < 0) bl = 0;
        if (bl > 255) bl = 255;

        return new Color(r, g, bl);
    }
}
