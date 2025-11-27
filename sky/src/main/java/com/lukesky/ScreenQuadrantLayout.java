package com.lukesky;

/**
 * ScreenQuadrantLayout — conceptual screen-space layout.
 *
 * Normalized coordinates:
 *   u ∈ [0,1] : left → right
 *   v ∈ [0,1] : top  → bottom
 *
 * Quadrants:
 *
 *   TOP_LEFT      : u ∈ [0, 0.5), v ∈ [0, 0.5)
 *   TOP_RIGHT     : u ∈ [0.5, 1.0), v ∈ [0, 0.5)
 *   BOTTOM_LEFT   : u ∈ [0, 0.5), v ∈ [0.5, 1.0)
 *   BOTTOM_RIGHT  : u ∈ [0.5, 1.0), v ∈ [0.5, 1.0)
 *
 * Map modes:
 *
 *   LIGHT : white + color 4-checker (highlight)
 *   SHADE : black + color 4-checker (shadow)
 *   COLOR : pure color (no checker modulation)
 *
 * COLOR covers both bottom quadrants to keep 3 distinct “vibes”.
 */
public final class ScreenQuadrantLayout {

    private ScreenQuadrantLayout() {}

    public enum Quadrant {
        TOP_LEFT,
        TOP_RIGHT,
        BOTTOM_LEFT,
        BOTTOM_RIGHT
    }

    public enum MapMode {
        LIGHT,
        SHADE,
        COLOR
    }

    public static Quadrant quadrantForUV(double u, double v) {
        if (u < 0.5) {
            if (v < 0.5) {
                return Quadrant.TOP_LEFT;
            } else {
                return Quadrant.BOTTOM_LEFT;
            }
        } else {
            if (v < 0.5) {
                return Quadrant.TOP_RIGHT;
            } else {
                return Quadrant.BOTTOM_RIGHT;
            }
        }
    }

    public static MapMode modeForQuadrant(Quadrant q) {
        switch (q) {
            case TOP_LEFT:
                return MapMode.LIGHT;
            case TOP_RIGHT:
                return MapMode.SHADE;
            case BOTTOM_LEFT:
                return MapMode.COLOR;
            case BOTTOM_RIGHT:
                return MapMode.COLOR;
            default:
                return MapMode.COLOR;
        }
    }

    public static MapMode modeForUV(double u, double v) {
        return modeForQuadrant(quadrantForUV(u, v));
    }
}
