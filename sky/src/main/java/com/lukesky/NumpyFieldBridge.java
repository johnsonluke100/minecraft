package com.lukesky;

import org.bukkit.plugin.Plugin;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.File;
import java.io.FileReader;

/**
 * NumpyFieldBridge
 *
 * Reads bpm_sync.json written by 8xd_mic_engine.command
 * and maps it into HarmonicFieldState.
 */
public class NumpyFieldBridge {

    private final Plugin plugin;
    private final File jsonFile;
    private final HarmonicFieldState state;
    private final JSONParser parser = new JSONParser();

    public NumpyFieldBridge(Plugin plugin, File jsonFile, HarmonicFieldState state) {
        this.plugin = plugin;
        this.jsonFile = jsonFile;
        this.state = state;
    }

    @SuppressWarnings("unchecked")
    public void tickReadJson() {
        if (jsonFile == null || !jsonFile.exists()) {
            return;
        }
        try (FileReader reader = new FileReader(jsonFile)) {
            Object parsed = parser.parse(reader);
            if (!(parsed instanceof JSONObject)) {
                return;
            }
            JSONObject root = (JSONObject) parsed;

            JSONObject audio = (JSONObject) root.get("audio");
            JSONObject hyper = (JSONObject) root.get("hypercube");

            float bpm    = safeFloat(audio, "bpm");
            float phase  = safeFloat(audio, "phase");
            float energy = safeFloat(audio, "energy");
            float bass   = safeFloat(audio, "bass");
            float mid    = safeFloat(audio, "mid");
            float high   = safeFloat(audio, "high");

            float a = safeFloat(hyper, "a");
            float b = safeFloat(hyper, "b");
            float c = safeFloat(hyper, "c");
            float d = safeFloat(hyper, "d");
            float e = safeFloat(hyper, "e");
            float f = safeFloat(hyper, "f");
            float g = safeFloat(hyper, "g");
            float z = safeFloat(hyper, "z");
            float y = safeFloat(hyper, "y");
            float x = safeFloat(hyper, "x");
            float w = safeFloat(hyper, "w");
            float v = safeFloat(hyper, "v");
            float u = safeFloat(hyper, "u");
            float t = safeFloat(hyper, "t");

            state.updateFromJson(
                    bpm, phase, energy, bass, mid, high,
                    a, b, c, d, e, f, g, z, y, x, w, v, u, t
            );

        } catch (Exception ex) {
            plugin.getLogger().warning("Failed to read bpm_sync.json: " + ex.getMessage());
        }
    }

    private float safeFloat(JSONObject obj, String key) {
        if (obj == null) return 0.0f;
        Object raw = obj.get(key);
        if (raw instanceof Number) {
            return ((Number) raw).floatValue();
        }
        return 0.0f;
    }
}
