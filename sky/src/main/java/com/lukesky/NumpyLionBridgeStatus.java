package com.lukesky;

import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;
import org.bukkit.scheduler.BukkitTask;

import java.io.File;

public class NumpyLionBridgeStatus {

    private final Plugin plugin;
    private final BeatVoiceBridge bridge;
    private BukkitTask task;

    private volatile double lastEnergy;
    private volatile double lastLion;
    private volatile long lastTimestamp;

    public NumpyLionBridgeStatus(Plugin plugin) {
        this.plugin = plugin;
        File jsonFile = new File(System.getProperty("user.home"), "Desktop/sky/bpm_sync.json");
        this.bridge = new BeatVoiceBridge(jsonFile);
        this.lastEnergy = 0.0D;
        this.lastLion = 0.0D;
        this.lastTimestamp = 0L;
    }

    public void start() {
        if (task != null) {
            return;
        }
        this.task = Bukkit.getScheduler().runTaskTimer(
                plugin,
                new Runnable() {
                    @Override
                    public void run() {
                        tick();
                    }
                },
                20L,
                5L
        );
    }

    public void stop() {
        if (task != null) {
            task.cancel();
            task = null;
        }
    }

    private void tick() {
        HarmonicFieldState state = bridge.sample();
        this.lastEnergy = bridge.getLastEnergy();
        this.lastLion = bridge.getLastLion();
        this.lastTimestamp = bridge.getLastReadTime();

        long age = getLastAgeMillis();
        if (age > 5000L) {
            plugin.getLogger().fine("NumPy JSON is stale (" + age + " ms). Lion still roars, but softly.");
        }
    }

    public double getLastEnergy() {
        return lastEnergy;
    }

    public double getLastLion() {
        return lastLion;
    }

    public long getLastTimestamp() {
        return lastTimestamp;
    }

    public long getLastAgeMillis() {
        long t = this.lastTimestamp;
        if (t <= 0L) {
            return Long.MAX_VALUE;
        }
        return System.currentTimeMillis() - t;
    }

    public BeatVoiceBridge getBridge() {
        return bridge;
    }
}
