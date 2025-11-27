package com.lukesky;

import org.bukkit.Bukkit;
import org.bukkit.Effect;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.entity.Player;
import org.bukkit.plugin.Plugin;
import org.bukkit.scheduler.BukkitTask;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

public class SphereSkyManager {

    private final Plugin plugin;
    private final NumpyLionBridgeStatus lionStatus;
    private final Set<UUID> enabledPlayers = new HashSet<UUID>();

    private BukkitTask task;

    public SphereSkyManager(Plugin plugin, NumpyLionBridgeStatus lionStatus) {
        this.plugin = plugin;
        this.lionStatus = lionStatus;
    }

    public void start() {
        if (task != null) {
            return;
        }

        this.task = Bukkit.getScheduler().runTaskTimer(
                plugin,
                new Runnable() {
                    private int tick = 0;

                    @Override
                    public void run() {
                        tick++;
                        tick = tick % 72000;
                        pulse(tick);
                    }
                },
                20L,
                2L
        );
    }

    public void stop() {
        if (task != null) {
            task.cancel();
            task = null;
        }
        enabledPlayers.clear();
    }

    public boolean togglePlayer(Player player) {
        UUID id = player.getUniqueId();
        if (enabledPlayers.contains(id)) {
            enabledPlayers.remove(id);
            return false;
        } else {
            enabledPlayers.add(id);
            return true;
        }
    }

    private void pulse(int tick) {
        if (enabledPlayers.isEmpty()) {
            return;
        }

        BeatVoiceBridge bridge = lionStatus.getBridge();
        HarmonicFieldState state = bridge.sample();

        double radius = state.skyRadius();
        int rings = state.supernovaRingCount();
        double rayDensity = state.rayDensity();
        double lionGlow = state.lionGlow();

        for (UUID id : enabledPlayers) {
            Player p = Bukkit.getPlayer(id);
            if (p == null || !p.isOnline()) {
                continue;
            }
            renderAroundPlayer(p, tick, radius, rings, rayDensity, lionGlow);
        }
    }

    private void renderAroundPlayer(Player player,
                                    int tick,
                                    double radius,
                                    int rings,
                                    double rayDensity,
                                    double lionGlow) {
        Location base = player.getLocation().clone();
        World world = base.getWorld();
        if (world == null) {
            return;
        }

        double yawRad = Math.toRadians(base.getYaw());
        double pitchRad = Math.toRadians(base.getPitch());

        double forwardX = -Math.sin(yawRad) * Math.cos(pitchRad);
        double forwardY = -Math.sin(pitchRad);
        double forwardZ = Math.cos(yawRad) * Math.cos(pitchRad);

        double beatPhase = ((double) (tick % 40)) / 40.0D;
        double beatPulse = 0.85D + 0.35D * Math.sin(beatPhase * 2.0D * Math.PI);
        double effectiveRadius = radius * beatPulse;

        int stepsPerRing = (int) Math.max(16, Math.round(effectiveRadius * 14.0D * rayDensity));
        double twoPi = Math.PI * 2.0D;

        double lionBand = 0.2D + lionGlow * 0.8D;
        int lionModulo = lionGlow > 0.6D ? 2 : 4;

        for (int r = 0; r < rings; r++) {
            double ringFrac = (double) r / Math.max(1.0D, (double) (rings - 1));
            double ringRadius = effectiveRadius * (0.25D + 0.75D * ringFrac);
            double ringYOffset = (ringFrac - 0.5D) * effectiveRadius * 0.5D;

            for (int i = 0; i < stepsPerRing; i++) {
                double angle = twoPi * (double) i / (double) stepsPerRing;

                double dirX = Math.cos(angle);
                double dirZ = Math.sin(angle);
                double dirY = Math.sin(angle * lionBand) * 0.3D;

                double dot = dirX * forwardX + dirY * forwardY + dirZ * forwardZ;
                if (dot < -0.2D) {
                    continue;
                }

                double px = base.getX() + dirX * ringRadius;
                double py = base.getY() + ringYOffset + dirY * ringRadius * 0.25D;
                double pz = base.getZ() + dirZ * ringRadius;

                Location loc = new Location(world, px, py, pz);

                if (lionGlow > 0.8D && (i % lionModulo == 0)) {
                    world.playEffect(loc, Effect.FIREWORKS_SPARK, 0);
                } else if (lionGlow > 0.4D && (i % 3 == 0)) {
                    world.playEffect(loc, Effect.ENCHANTMENT_TABLE, 0);
                } else {
                    world.playEffect(loc, Effect.CLOUD, 0);
                }
            }
        }
    }
}
