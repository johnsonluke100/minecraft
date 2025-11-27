package com.lukesky;

public class WormholeVortex {

    private final double rotation;
    private final double spiral;
    private final double depth;
    private final double fold;

    public WormholeVortex(double rotation, double spiral, double depth, double fold) {
        this.rotation = clamp(rotation);
        this.spiral   = clamp(spiral);
        this.depth    = clamp(depth);
        this.fold     = clamp(fold);
    }

    private static double clamp(double v) {
        if (v < 0.0) return 0.0;
        if (v >= 1.0) return 0.999999999999;
        return v;
    }

    public double getRotation() { return rotation; }
    public double getSpiral()   { return spiral; }
    public double getDepth()    { return depth; }
    public double getFold()     { return fold; }

    public double lens(double x) {
        double r = rotation * 0.6;
        double s = spiral * 0.8;
        double d = depth * 0.45;
        double f = fold * 0.25;

        double warp = Math.sin(x * Math.PI * 2.0 * (1.0 + s))
                    * Math.cos(x * Math.PI * r)
                    + Math.sin(d * 6.0 * x)
                    + Math.cos(f + x * 12.0);

        return warp * 0.33;
    }
}
