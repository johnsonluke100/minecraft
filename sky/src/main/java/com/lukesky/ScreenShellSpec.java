package com.lukesky;

/**
 * ScreenShellSpec
 *
 * A pure-data description of how many maps are needed
 * to approximate the player's screen with 4-checker map tiles.
 *
 * Resolution input comes from client/resolution.json on disk,
 * but this class stays pure Java (no file IO).
 */
public final class ScreenShellSpec {

    private final int width;
    private final int height;
    private final int quadrantWidth;
    private final int quadrantHeight;
    private final int mapsPerSide;

    public ScreenShellSpec(int width,
                           int height,
                           int mapsPerSide) {
        this.width = width;
        this.height = height;
        this.mapsPerSide = mapsPerSide;

        this.quadrantWidth = width / 4;
        this.quadrantHeight = height / 4;
    }

    public int getWidth() {
        return width;
    }

    public int getHeight() {
        return height;
    }

    public int getQuadrantWidth() {
        return quadrantWidth;
    }

    public int getQuadrantHeight() {
        return quadrantHeight;
    }

    public int getMapsPerSide() {
        return mapsPerSide;
    }

    public int getTotalMaps() {
        int perQuadrant = mapsPerSide * mapsPerSide;
        return perQuadrant * 4;
    }
}
