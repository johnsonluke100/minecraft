package com.lukesky;

import java.awt.Color;
import java.util.HashMap;
import java.util.Map;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;

/**
 * MapShadingEngine
 *
 * This is the literal "light cast + shadow" calculator.
 * It takes:
 *   - a 14D axis array
 *   - a discSpin value (0..1)
 *
 * and produces a 4-checker pattern:
 *   [C0, C1, C2, C3] = [light, lightHighlight, shadow, shadowDeep]
 *
 * For Sequence 6, this is still pure math — not yet writing to
 * actual map pixels. The invisible armor-stand map shell will
 * live in a later sequence.
 */
public final class MapShadingEngine {

    private final Map<String, MapColorProfile> profiles = new HashMap<String, MapColorProfile>();
    private MapColorProfile active;
    private final double shadowStrength;
    private final double lightStrength;

    public MapShadingEngine(FileConfiguration config) {
        ConfigurationSection maplight = config.getConfigurationSection("maplight");
        if (maplight == null) {
            active = defaultProfile();
            shadowStrength = 0.7;
            lightStrength = 0.9;
            return;
        }

        shadowStrength = maplight.getDouble("shadow_strength", 0.7);
        lightStrength  = maplight.getDouble("light_strength", 0.9);

        ConfigurationSection schemes = maplight.getConfigurationSection("schemes");
        if (schemes != null) {
            for (String key : schemes.getKeys(false)) {
                ConfigurationSection s = schemes.getConfigurationSection(key);
                if (s == null) continue;
                String id = s.getString("id", key);

                Color lightColor = parseColor(s.getString("light_color", "#ff00ff"));
                Color lightHighlight = parseColor(s.getString("light_highlight", "#ffffff"));
                Color shadowColor = parseColor(s.getString("shadow_color", "#00ffff"));
                Color shadowDeep = parseColor(s.getString("shadow_deep", "#000000"));

                MapColorProfile profile = new MapColorProfile(
                        id,
                        lightColor,
                        lightHighlight,
                        shadowColor,
                        shadowDeep
                );
                profiles.put(id, profile);
            }
        }

        String defId = maplight.getString("default_scheme", "magenta_cyan_missing");
        MapColorProfile def = profiles.get(defId);
        if (def == null) def = defaultProfile();
        active = def;
    }

    private static Color parseColor(String hex) {
        if (hex == null) return Color.MAGENTA;
        String h = hex.trim();
        if (h.startsWith("#")) {
            h = h.substring(1);
        }
        if (h.length() == 3) {
            char r = h.charAt(0);
            char g = h.charAt(1);
            char b = h.charAt(2);
            h = "" + r + r + g + g + b + b;
        }
        if (h.length() != 6) {
            return Color.MAGENTA;
        }
        try {
            int rgb = Integer.parseInt(h, 16);
            return new Color(rgb);
        } catch (NumberFormatException ex) {
            return Color.MAGENTA;
        }
    }

    private static MapColorProfile defaultProfile() {
        Color magenta = new Color(0xFF00FF);
        Color cyan    = new Color(0x00FFFF);
        return new MapColorProfile(
                "magenta_cyan_missing",
                magenta,
                Color.WHITE,
                cyan,
                Color.BLACK
        );
    }

    /**
     * Given axes14 (0..1) and discSpin (0..1), return a 4-length array:
     *   [lightPixel, lightHighlightPixel, shadowPixel, shadowDeepPixel]
     *
     * For now this is just Colors, kept abstracted from actual map palettes.
     */
    public Color[] samplePattern(double[] axes14, double discSpin) {
        if (axes14 == null || axes14.length != 14) {
            axes14 = new double[14];
        }
        if (discSpin < 0.0) discSpin = 0.0;
        if (discSpin > 1.0) discSpin = 1.0;

        double east = axes14[7];   // a
        double north = axes14[8];  // b
        double west = axes14[9];   // c
        double south = axes14[10]; // d
        double poleN = axes14[11]; // e
        double poleS = axes14[12]; // f
        double g = axes14[13];     // expansion

        double hemiLR = (east + west) / 2.0;
        double hemiNS = (north + south) / 2.0;
        double poleBlend = (poleN + poleS) / 2.0;

        double lightSeed  = clamp01(0.5 * hemiLR + 0.25 * poleBlend + 0.25 * discSpin);
        double shadowSeed = clamp01(0.5 * hemiNS + 0.25 * poleBlend + 0.25 * (1.0 - discSpin));

        double lightT  = lightSeed * lightStrength;
        double shadowT = shadowSeed * shadowStrength;

        Color c0 = active.blendLight(lightT);
        Color c1 = active.blendLight(clamp01(lightT + 0.2));
        Color c2 = active.blendShadow(shadowT);
        Color c3 = active.blendShadow(clamp01(shadowT + 0.2));

        return new Color[]{ c0, c1, c2, c3 };
    }

    private static double clamp01(double v) {
        if (v < 0.0) return 0.0;
        if (v > 1.0) return 1.0;
        return v;
    }

    public MapColorProfile getActiveProfile() {
        return active;
    }
}
