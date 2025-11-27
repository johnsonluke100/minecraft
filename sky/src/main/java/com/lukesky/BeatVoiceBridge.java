package com.lukesky;

import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.logging.Logger;

/**
 * BeatVoiceBridge:
 *  - Periodically reads bpm_sync.json written by the NumPy engine.
 *  - Parses vec14, energy, phase, superposition, lion.
 *  - Pushes into HarmonicFieldState.
 *
 * No external JSON library: naive, stable string parsing
 * tailored to the known shape of the file.
 */
public final class BeatVoiceBridge {

    private final Plugin plugin;
    private final File jsonFile;
    private final Logger log;

    public BeatVoiceBridge(Plugin plugin, File jsonFile) {
        this.plugin = plugin;
        this.jsonFile = jsonFile;
        this.log = plugin.getLogger();
    }

    public void start() {
        // Run every 2 ticks (approx 10ms on 20 TPS server)
        Bukkit.getScheduler().runTaskTimerAsynchronously(plugin, new Runnable() {
            @Override
            public void run() {
                tick();
            }
        }, 20L, 2L);
    }

    private void tick() {
        if (!jsonFile.exists()) {
            return;
        }
        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new FileReader(jsonFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line);
            }
        } catch (Exception ex) {
            log.fine("[SkyLighting] JSON read failed: " + ex.getMessage());
            return;
        }

        String raw = sb.toString().trim();
        if (raw.isEmpty()) return;

        try {
            double energy = parseDoubleField(raw, "\"energy\":");
            double phase = parseDoubleField(raw, "\"phase\":");
            double superposition = parseDoubleField(raw, "\"superposition\":");
            double lion = parseDoubleField(raw, "\"lion\":");

            double[] vec14 = parseVec14(raw);

            HarmonicFieldState.update(vec14, energy, phase, superposition, lion);
        } catch (Exception ex) {
            log.fine("[SkyLighting] JSON parse failed: " + ex.getMessage());
        }
    }

    private static double parseDoubleField(String raw, String key) {
        int idx = raw.indexOf(key);
        if (idx < 0) return 0.0;
        int start = idx + key.length();
        int end = start;
        while (end < raw.length() &&
               "0123456789+-.eE".indexOf(raw.charAt(end)) >= 0) {
            end++;
        }
        String num = raw.substring(start, end).trim();
        if (num.isEmpty()) return 0.0;
        return Double.parseDouble(num);
    }

    private static double[] parseVec14(String raw) {
        String key = "\"vec14\":";
        int idx = raw.indexOf(key);
        double[] result = new double[14];
        if (idx < 0) return result;

        int start = raw.indexOf('[', idx);
        int end   = raw.indexOf(']', start);
        if (start < 0 || end < 0) return result;

        String inside = raw.substring(start + 1, end);
        String[] parts = inside.split(",");
        int len = Math.min(parts.length, 14);
        for (int i = 0; i < len; i++) {
            try {
                result[i] = Double.parseDouble(parts[i].trim());
            } catch (Exception ignored) {
                result[i] = 0.0;
            }
        }
        return result;
    }
}
