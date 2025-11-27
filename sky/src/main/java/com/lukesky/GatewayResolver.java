package com.lukesky;

import java.io.File;
import java.io.FileReader;
import java.util.Arrays;
import org.bukkit.entity.Player;

/**
 * GatewayResolver
 *
 * Determines whether a player's 14-axis continuum state matches
 * the Vortex signature that opens the sole Nether portal.
 *
 * If the player exactly hits the specified 14 floats:
 *    0.1,0,0,0,0,0,0.1,0.1,0,0,0,0,0,0.1
 *
 * the gateway "opens" (Main.java handles teleport scheduling).
 */
public final class GatewayResolver {

    private final double[] vortex;

    public GatewayResolver(File file) {
        double[] fallback = new double[]{
            0.1,0,0,0,0,0,0.1,0.1,0,0,0,0,0,0.1
        };
        double[] read = fallback;

        try (FileReader fr = new FileReader(file)) {
            StringBuilder sb = new StringBuilder();
            int c;
            while ((c = fr.read()) != -1) {
                sb.append((char)c);
            }
            String txt = sb.toString();
            int idx = txt.indexOf("[");
            int jdx = txt.indexOf("]");
            if (idx != -1 && jdx != -1) {
                String list = txt.substring(idx+1, jdx);
                String[] parts = list.split(",");
                if (parts.length == 14) {
                    double[] arr = new double[14];
                    for (int i = 0; i < 14; i++) {
                        arr[i] = Double.parseDouble(parts[i].trim());
                    }
                    read = arr;
                }
            }
        } catch (Exception e) {
            read = fallback;
        }

        this.vortex = read;
    }

    public boolean isVortex(double[] axes) {
        if (axes == null || axes.length != 14) return false;

        double tol = 0.0000001;
        for (int i = 0; i < 14; i++) {
            if (Math.abs(axes[i] - vortex[i]) > tol) {
                return false;
            }
        }
        return true;
    }

    public boolean isVortex(Player p) {
        double[] cur = HypercubeRegistry.getAxes(p.getUniqueId().toString());
        return isVortex(cur);
    }

    public double[] getSignature() {
        return Arrays.copyOf(vortex, vortex.length);
    }
}
