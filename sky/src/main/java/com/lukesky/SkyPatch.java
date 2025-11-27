package com.lukesky;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.entity.Player;
import org.bukkit.Particle;

/**
 * SkyPatch:
 *  - Simple visual sampler of the 14-float continuum.
 *  - Draws a soft grounded halo around each player based on energy + lion.
 *
 * This is intentionally minimal and stable. It can be expanded later
 * into your full wormhole / supernova engine.
 */
public final class SkyPatch {

    private SkyPatch() {}

    public static void start() {
        // Render every 5 ticks
        Bukkit.getScheduler().runTaskTimer(
                Bukkit.getPluginManager().getPlugin("SkyLighting"),
                new Runnable() {
                    @Override
                    public void run() {
                        tick();
                    }
                },
                40L,
                5L
        );
    }

    private static void tick() {
        double[] v = HarmonicFieldState.snapshotVec14();
        double energy = HarmonicFieldState.getEnergy();
        double lion   = HarmonicFieldState.getLion();

        double radius = 0.6 + energy * 1.4;
        int particles = (int) (24 + lion * 64);

        for (Player p : Bukkit.getOnlinePlayers()) {
            World w = p.getWorld();
            Location base = p.getLocation().clone().add(0, 1.4, 0);

            for (int i = 0; i < particles; i++) {
                double angle = (2 * Math.PI * i) / particles;
                double x = radius * Math.cos(angle);
                double z = radius * Math.sin(angle);
                Location spot = base.clone().add(x, 0, z);

                w.spawnParticle(
                        Particle.REDSTONE,
                        spot,
                        0,
                        0.0, 0.0, 0.0,
                        1.0
                );
            }
        }
    }
}
