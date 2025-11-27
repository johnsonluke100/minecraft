package com.lukesky;

/**
 * Thread-safe holder for the current audio ⇄ sky continuum state.
 *
 * All values are clamped to [0, 0.999999999999].
 *  - vec14: 14-dimensional continuum floats
 *  - energy, phase, superposition, lion: scalar views
 */
public final class HarmonicFieldState {

    private static final Object LOCK = new Object();

    private static double[] vec14 = new double[14];
    private static double energy  = 0.0;
    private static double phase   = 0.0;
    private static double superposition = 0.0;
    private static double lion    = 0.0;

    private static double clamp01(double v) {
        if (v < 0.0) return 0.0;
        if (v >= 1.0) return 0.999999999999;
        return v;
    }

    public static void update(double[] newVec14,
                              double newEnergy,
                              double newPhase,
                              double newSuperposition,
                              double newLion) {
        if (newVec14 == null || newVec14.length != 14) return;

        synchronized (LOCK) {
            for (int i = 0; i < 14; i++) {
                vec14[i] = clamp01(newVec14[i]);
            }
            energy        = clamp01(newEnergy);
            phase         = clamp01(newPhase);
            superposition = clamp01(newSuperposition);
            lion          = clamp01(newLion);
        }
    }

    public static double[] snapshotVec14() {
        synchronized (LOCK) {
            double[] copy = new double[14];
            System.arraycopy(vec14, 0, copy, 0, 14);
            return copy;
        }
    }

    public static double getEnergy() {
        synchronized (LOCK) {
            return energy;
        }
    }

    public static double getPhase() {
        synchronized (LOCK) {
            return phase;
        }
    }

    public static double getSuperposition() {
        synchronized (LOCK) {
            return superposition;
        }
    }

    public static double getLion() {
        synchronized (LOCK) {
            return lion;
        }
    }
}
