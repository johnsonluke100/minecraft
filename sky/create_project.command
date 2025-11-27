#!/bin/bash
set -euo pipefail

########################################################################
#  MINECRAFT 8XD — QUADRANT LIGHT/SHADE/COLOR • FRAME PING LAYER 3
#
#  Focus of this pass:
#    • Still divide the logical “screen” into 4 quadrants
#    • Still only compute 1/4 of the client pixel grid per frame (concept)
#    • Deepen 2-way ping per frame:
#         - Player → /skyres <w> <h> and /skyframe
#         - Java   → screen_quadrant_request.json (per frame)
#         - NumPy  → screen_quadrant_layout.json + screen_colormap_8xd.json
#    • 3 map quadrant types: LIGHT, SHADE, COLOR
#         - keep checker patterns for LIGHT/SHADE
#         - pure color for COLOR
#
#  This script REPLACES the existing create_project.command.
#  Run from macOS terminal:
#
#    cd ~/Desktop/sky
#    chmod +x create_project.command
#    ./create_project.command
########################################################################

OS_NAME="$(uname -s || echo "Unknown")"
if [ "$OS_NAME" != "Darwin" ]; then
  echo "This script is tuned for macOS (Darwin)." 1>&2
  exit 1
fi

DESKTOP="${HOME}/Desktop"
SKY_ROOT="${DESKTOP}/sky"
SRC_MAIN="${SKY_ROOT}/src/main/java/com/lukesky"
RES_MAIN="${SKY_ROOT}/src/main/resources"

mkdir -p "${SKY_ROOT}" "${SRC_MAIN}" "${RES_MAIN}"

echo "-------------------------------------------------------"
echo "  8XD — QUADRANT FRAME PING • LAYER 3"
echo "-------------------------------------------------------"
echo "Sky root : ${SKY_ROOT}"
echo "Intent   : 4 quadrants • 1/4 pixels • LIGHT/SHADE/COLOR maps"
echo "           + explicit /skyframe 2-way frame ping"
echo "-------------------------------------------------------"
echo

########################################################################
# 1) pom.xml — Spigot 1.8.8 API base
########################################################################

cat << 'EOF' > "${SKY_ROOT}/pom.xml"
<!-- 8XD Quadrant Frame Ping Sky Engine POM (Layer 3) -->
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>
    <groupId>com.lukesky</groupId>
    <artifactId>SkyLighting</artifactId>
    <version>1.0-SNAPSHOT</version>

    <name>SkyLighting</name>
    <description>
      8XD Quadrant Frame Ping Sky Engine (Layer 3).

      Java / Spigot:
        • /skyomega  → omega scalar via digit reversal
        • /skyquad   → quadrant + LIGHT/SHADE/COLOR mode
        • /skyres    → client resolution ping (width/height)
        • /skyframe  → explicit frame ping (2-way per-frame handshake)
        • ResolutionState: per-player width/height + frame index
        • QuadrantFrameExporter: writes screen_quadrant_request.json

      Python / NumPy:
        • screen_quadrant_mapper.py
             - consumes player_resolution.json
             - uses screen_quadrant_request.json (frame, player tag)
             - computes quarter tile (TOP_LEFT) geometry
        • screen_colormap_generator.py
             - LIGHT  : white + color 4-checker
             - SHADE  : black + color 4-checker
             - COLOR  : pure color
        • quadrant_channel_splitter.py
             - splits LIGHT/SHADE/COLOR into separate 0–1 channels.
    </description>

    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <repositories>
        <repository>
          <id>spigot-repo</id>
          <url>https://hub.spigotmc.org/nexus/content/repositories/snapshots/</url>
        </repository>
    </repositories>

    <dependencies>
        <dependency>
          <groupId>org.spigotmc</groupId>
          <artifactId>spigot-api</artifactId>
          <version>1.8.8-R0.1-SNAPSHOT</version>
          <scope>provided</scope>
        </dependency>
    </dependencies>

</project>
EOF

echo "✔ pom.xml written"

########################################################################
# 2) plugin.yml — include /skyframe
########################################################################

cat << 'EOF' > "${RES_MAIN}/plugin.yml"
name: SkyLighting
main: com.lukesky.Main
version: 1.0
author: Luke
description: >
  8XD Quadrant Frame Ping Sky Engine (Layer 3).
  LIGHT / SHADE / COLOR quadrants; NumPy backend sky.

commands:
  skyomega:
    description: Show your current omega scalar and fade.
    usage: /<command>
    permission: skylighting.omega
  skyquad:
    description: Show quadrant + LIGHT/SHADE/COLOR mode for you.
    usage: /<command>
    permission: skylighting.quadrant
  skyres:
    description: Tell the server your screen resolution (width height).
    usage: /<command> <width> <height>
    permission: skylighting.resolution
  skyframe:
    description: Explicitly ping a frame; updates frame index and writes screen_quadrant_request.json.
    usage: /<command>
    permission: skylighting.frame

permissions:
  skylighting.omega:
    description: Use /skyomega omega debug command.
    default: true
  skylighting.quadrant:
    description: Use /skyquad to inspect quadrant layout and modes.
    default: true
  skylighting.resolution:
    description: Use /skyres to send your resolution “ping up”.
    default: true
  skylighting.frame:
    description: Use /skyframe for explicit frame pings.
    default: true
EOF

echo "✔ plugin.yml written"

########################################################################
# 3) NumpyCoordBridge — digit reversal scalar in [0,1)
########################################################################

cat << 'EOF' > "${SRC_MAIN}/NumpyCoordBridge.java"
package com.lukesky;

import org.bukkit.Location;
import org.bukkit.entity.Player;

/**
 * NumpyCoordBridge — Java mirror of the digit-reversal scalar.
 *
 * Rule:
 *   1) Use |z| (block Z coord) in base-10.
 *   2) Reverse digits as string.
 *   3) Interpret "rev" as "0.rev" in decimal.
 *   4) Clamp into [0, 1) (never exactly 1.0).
 *
 * Examples:
 *
 *   (0,0,1)   → "1"   → "1"   → 0.1
 *   (0,0,10)  → "10"  → "01"  → 0.01
 *   (0,0,369) → "369" → "963" → 0.963
 *   (0,0,248) → "248" → "842" → 0.842
 */
public final class NumpyCoordBridge {

    private NumpyCoordBridge() {}

    public static double encodeScalar(int x, int y, int z) {
        return reversedUnit(z);
    }

    private static double reversedUnit(int n) {
        n = Math.abs(n);
        String s = Integer.toString(n);
        String rev = new StringBuilder(s).reverse().toString();
        String dec = "0." + rev;

        double value;
        try {
            value = Double.parseDouble(dec);
        } catch (NumberFormatException e) {
            value = 0.0;
        }

        if (value < 0.0) {
            value = 0.0;
        }
        if (value >= 1.0) {
            value = 0.999999999999d;
        }
        return value;
    }

    public static double encodeFromPlayer(Player player) {
        if (player == null) {
            return 0.0;
        }
        Location loc = player.getLocation();
        return encodeScalar(loc.getBlockX(), loc.getBlockY(), loc.getBlockZ());
    }
}
EOF

echo "✔ NumpyCoordBridge.java written"

########################################################################
# 4) OmegaMirrorField — scalar → fade
########################################################################

cat << 'EOF' > "${SRC_MAIN}/OmegaMirrorField.java"
package com.lukesky;

import org.bukkit.entity.Player;

/**
 * OmegaMirrorField — scalar → fade.
 *
 * Simple easing:
 *   fade = scalar^2, clamped into [0, 1).
 */
public final class OmegaMirrorField {

    private OmegaMirrorField() {}

    public static double sampleScalar(Player player) {
        return NumpyCoordBridge.encodeFromPlayer(player);
    }

    public static float sampleFade(Player player) {
        double s = sampleScalar(player);
        double eased = s * s;
        if (eased >= 1.0) {
            eased = 0.9999999d;
        }
        return (float) eased;
    }
}
EOF

echo "✔ OmegaMirrorField.java written"

########################################################################
# 5) ScreenQuadrantLayout — 4 quadrants, 3 map modes
########################################################################

cat << 'EOF' > "${SRC_MAIN}/ScreenQuadrantLayout.java"
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
EOF

echo "✔ ScreenQuadrantLayout.java written"

########################################################################
# 6) ResolutionState — per-player width/height + frame index
########################################################################

cat << 'EOF' > "${SRC_MAIN}/ResolutionState.java"
package com.lukesky;

import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * ResolutionState — stores per-player resolution and frame index.
 *
 * Java-side half of a “2-way packet ping per frame”:
 *
 *   • Client calls /skyres <width> <height> → sends res “up”.
 *   • Server stores ResolutionSnapshot and increments frame index on /skyframe.
 *   • NumPy backend reads player_resolution.json + screen_quadrant_request.json
 *     to compute only 1/4 of the pixel grid for that frame.
 */
public final class ResolutionState {

    private static final ConcurrentHashMap<UUID, ResolutionSnapshot> STATE =
            new ConcurrentHashMap<UUID, ResolutionSnapshot>();

    public static void setResolution(UUID uuid, int width, int height) {
        ResolutionSnapshot snapshot = STATE.get(uuid);
        if (snapshot == null) {
            snapshot = new ResolutionSnapshot(width, height, 0L);
        } else {
            snapshot = new ResolutionSnapshot(width, height, snapshot.getFrameIndex());
        }
        STATE.put(uuid, snapshot);
    }

    public static ResolutionSnapshot getOrDefault(UUID uuid) {
        ResolutionSnapshot snapshot = STATE.get(uuid);
        if (snapshot == null) {
            snapshot = new ResolutionSnapshot(1920, 1080, 0L);
            STATE.put(uuid, snapshot);
        }
        return snapshot;
    }

    public static ResolutionSnapshot incrementFrame(UUID uuid) {
        ResolutionSnapshot snapshot = getOrDefault(uuid);
        long next = snapshot.getFrameIndex() + 1L;
        ResolutionSnapshot updated = new ResolutionSnapshot(
                snapshot.getWidth(),
                snapshot.getHeight(),
                next
        );
        STATE.put(uuid, updated);
        return updated;
    }

    public static final class ResolutionSnapshot {
        private final int width;
        private final int height;
        private final long frameIndex;

        public ResolutionSnapshot(int width, int height, long frameIndex) {
            this.width = width;
            this.height = height;
            this.frameIndex = frameIndex;
        }

        public int getWidth() {
            return width;
        }

        public int getHeight() {
            return height;
        }

        public long getFrameIndex() {
            return frameIndex;
        }
    }

    private ResolutionState() {}
}
EOF

echo "✔ ResolutionState.java written"

########################################################################
# 7) ScreenResolutionCommand — /skyres <w> <h>
########################################################################

cat << 'EOF' > "${SRC_MAIN}/ScreenResolutionCommand.java"
package com.lukesky;

import com.lukesky.ResolutionState.ResolutionSnapshot;
import org.bukkit.ChatColor;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.UUID;

/**
 * /skyres <width> <height> — client “ping up” of screen resolution.
 *
 * Side-effects:
 *
 *   • Stores ResolutionSnapshot in memory (frameIndex unchanged).
 *   • Writes player_resolution.json into the server root (plugins/..).
 */
public final class ScreenResolutionCommand implements CommandExecutor {

    private final Main plugin;

    public ScreenResolutionCommand(Main plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(
            CommandSender sender,
            Command command,
            String label,
            String[] args
    ) {
        if (!(sender instanceof Player)) {
            sender.sendMessage(ChatColor.RED + "Only players can use /skyres.");
            return true;
        }

        Player player = (Player) sender;
        UUID uuid = player.getUniqueId();

        if (args.length != 2) {
            sender.sendMessage(ChatColor.RED + "Usage: /skyres <width> <height>");
            return true;
        }

        int width;
        int height;

        try {
            width = Integer.parseInt(args[0]);
            height = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            sender.sendMessage(ChatColor.RED + "Width and height must be integers.");
            return true;
        }

        if (width <= 0 || height <= 0) {
            sender.sendMessage(ChatColor.RED + "Width and height must be positive.");
            return true;
        }

        ResolutionState.setResolution(uuid, width, height);
        ResolutionSnapshot snapshot = ResolutionState.getOrDefault(uuid);
        writeResolutionJson(snapshot);

        sender.sendMessage(ChatColor.GREEN + "---- 8XD Screen Resolution Ping ----");
        sender.sendMessage(ChatColor.GOLD + "Width : " + ChatColor.YELLOW + snapshot.getWidth());
        sender.sendMessage(ChatColor.GOLD + "Height: " + ChatColor.YELLOW + snapshot.getHeight());
        sender.sendMessage(ChatColor.GOLD + "Frame : " + ChatColor.AQUA + snapshot.getFrameIndex());
        sender.sendMessage(ChatColor.GREEN + "Resolution locked in; ready for quadrant mapping.");
        sender.sendMessage(ChatColor.GREEN + "-------------------------------------");

        return true;
    }

    private void writeResolutionJson(ResolutionState.ResolutionSnapshot snapshot) {
        File plugins = plugin.getDataFolder().getParentFile();
        File root = plugins.getParentFile();
        if (!root.exists()) {
            root.mkdirs();
        }

        File outFile = new File(root, "player_resolution.json");
        FileWriter writer = null;
        try {
            writer = new FileWriter(outFile, false);
            writer.write("{\n");
            writer.write("  \"width\": " + snapshot.getWidth() + ",\n");
            writer.write("  \"height\": " + snapshot.getHeight() + ",\n");
            writer.write("  \"frameIndex\": " + snapshot.getFrameIndex() + "\n");
            writer.write("}\n");
        } catch (IOException e) {
            plugin.getLogger().warning("Failed to write player_resolution.json: " + e.getMessage());
        } finally {
            if (writer != null) {
                try { writer.close(); } catch (IOException ignored) {}
            }
        }
    }
}
EOF

echo "✔ ScreenResolutionCommand.java written"

########################################################################
# 8) OmegaDebugCommand — /skyomega
########################################################################

cat << 'EOF' > "${SRC_MAIN}/OmegaDebugCommand.java"
package com.lukesky;

import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

public final class OmegaDebugCommand implements CommandExecutor {

    private final Main plugin;

    public OmegaDebugCommand(Main plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(
            CommandSender sender,
            Command command,
            String label,
            String[] args
    ) {
        if (!(sender instanceof Player)) {
            sender.sendMessage(ChatColor.RED + "Only players can use /skyomega.");
            return true;
        }

        Player player = (Player) sender;
        Location loc = player.getLocation();

        double scalar = NumpyCoordBridge.encodeFromPlayer(player);
        float fade = OmegaMirrorField.sampleFade(player);

        player.sendMessage(ChatColor.AQUA + "---- 8XD Omega Mirror ----");
        player.sendMessage(ChatColor.GOLD + "XYZ: "
                + ChatColor.YELLOW + loc.getBlockX() + ", "
                + loc.getBlockY() + ", "
                + loc.getBlockZ());
        player.sendMessage(ChatColor.GOLD + "Omega scalar (digit-reversal): "
                + ChatColor.GREEN + String.format("%.12f", scalar));
        player.sendMessage(ChatColor.GOLD + "Omega fade (scalar^2): "
                + ChatColor.GREEN + String.format("%.6f", fade));
        player.sendMessage(ChatColor.AQUA + "---------------------------");

        return true;
    }
}
EOF

echo "✔ OmegaDebugCommand.java written"

########################################################################
# 9) QuadrantDebugCommand — /skyquad
########################################################################

cat << 'EOF' > "${SRC_MAIN}/QuadrantDebugCommand.java"
package com.lukesky;

import com.lukesky.ScreenQuadrantLayout.MapMode;
import com.lukesky.ScreenQuadrantLayout.Quadrant;
import com.lukesky.ResolutionState.ResolutionSnapshot;
import org.bukkit.ChatColor;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

/**
 * /skyquad — show conceptual (u, v), quadrant, map mode, and frame index.
 *
 * Normalized coordinates (for now) are derived from omega scalar:
 *
 *   u = scalar
 *   v = 1 - scalar
 */
public final class QuadrantDebugCommand implements CommandExecutor {

    private final Main plugin;

    public QuadrantDebugCommand(Main plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(
            CommandSender sender,
            Command command,
            String label,
            String[] args
    ) {
        if (!(sender instanceof Player)) {
            sender.sendMessage(ChatColor.RED + "Only players can use /skyquad.");
            return true;
        }

        Player player = (Player) sender;
        double scalar = NumpyCoordBridge.encodeFromPlayer(player);

        double u = scalar;
        double v = 1.0 - scalar;

        Quadrant quadrant = ScreenQuadrantLayout.quadrantForUV(u, v);
        MapMode mode = ScreenQuadrantLayout.modeForQuadrant(quadrant);

        ResolutionSnapshot snapshot = ResolutionState.getOrDefault(player.getUniqueId());

        sender.sendMessage(ChatColor.LIGHT_PURPLE + "---- 8XD Quadrant Frame Ping ----");
        sender.sendMessage(ChatColor.GOLD + "u (normalized x): "
                + ChatColor.GREEN + String.format("%.6f", u));
        sender.sendMessage(ChatColor.GOLD + "v (normalized y): "
                + ChatColor.GREEN + String.format("%.6f", v));
        sender.sendMessage(ChatColor.GOLD + "Quadrant: "
                + ChatColor.AQUA + quadrant.name());
        sender.sendMessage(ChatColor.GOLD + "Map mode: "
                + ChatColor.AQUA + mode.name());
        sender.sendMessage(ChatColor.GOLD + "Width x Height: "
                + ChatColor.YELLOW + snapshot.getWidth()
                + ChatColor.GRAY + " x "
                + ChatColor.YELLOW + snapshot.getHeight());
        sender.sendMessage(ChatColor.GOLD + "Frame index: "
                + ChatColor.AQUA + snapshot.getFrameIndex());
        sender.sendMessage(ChatColor.LIGHT_PURPLE + "My vision is the vibe, my hearing is the vibe.");
        sender.sendMessage(ChatColor.LIGHT_PURPLE + "-----------------------------------");
        return true;
    }
}
EOF

echo "✔ QuadrantDebugCommand.java written"

########################################################################
# 10) QuadrantFrameExporter — /skyframe
########################################################################

cat << 'EOF' > "${SRC_MAIN}/QuadrantFrameExporter.java"
package com.lukesky;

import com.lukesky.ResolutionState.ResolutionSnapshot;
import org.bukkit.ChatColor;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.UUID;

/**
 * /skyframe — explicit frame ping for 2-way packet handshake.
 *
 * Side-effects:
 *
 *   • Increments frame index in ResolutionState for this player.
 *   • Writes screen_quadrant_request.json into server root:
 *        {
 *          "player": "<name>",
 *          "uuid": "<uuid>",
 *          "width": <w>,
 *          "height": <h>,
 *          "frameIndex": <n>
 *        }
 *
 * NumPy scripts then:
 *   - read player_resolution.json
 *   - read screen_quadrant_request.json
 *   - compute quarter pixel grid for that frame only.
 */
public final class QuadrantFrameExporter implements CommandExecutor {

    private final Main plugin;

    public QuadrantFrameExporter(Main plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(
            CommandSender sender,
            Command command,
            String label,
            String[] args
    ) {
        if (!(sender instanceof Player)) {
            sender.sendMessage(ChatColor.RED + "Only players can use /skyframe.");
            return true;
        }

        Player player = (Player) sender;
        UUID uuid = player.getUniqueId();

        ResolutionSnapshot snapshot = ResolutionState.incrementFrame(uuid);
        writeFrameRequest(player, snapshot);

        sender.sendMessage(ChatColor.BLUE + "---- 8XD FRAME PING ----");
        sender.sendMessage(ChatColor.GOLD + "Player     : " + ChatColor.AQUA + player.getName());
        sender.sendMessage(ChatColor.GOLD + "Resolution : "
                + ChatColor.YELLOW + snapshot.getWidth()
                + ChatColor.GRAY + " x "
                + ChatColor.YELLOW + snapshot.getHeight());
        sender.sendMessage(ChatColor.GOLD + "FrameIndex : "
                + ChatColor.AQUA + snapshot.getFrameIndex());
        sender.sendMessage(ChatColor.BLUE + "screen_quadrant_request.json updated.");
        sender.sendMessage(ChatColor.BLUE + "--------------------------");

        return true;
    }

    private void writeFrameRequest(Player player, ResolutionSnapshot snapshot) {
        File plugins = plugin.getDataFolder().getParentFile();
        File root = plugins.getParentFile();
        if (!root.exists()) {
            root.mkdirs();
        }

        File outFile = new File(root, "screen_quadrant_request.json");
        FileWriter writer = null;
        try {
            writer = new FileWriter(outFile, false);
            writer.write("{\n");
            writer.write("  \"player\": \"" + safe(player.getName()) + "\",\n");
            writer.write("  \"uuid\": \"" + player.getUniqueId().toString() + "\",\n");
            writer.write("  \"width\": " + snapshot.getWidth() + ",\n");
            writer.write("  \"height\": " + snapshot.getHeight() + ",\n");
            writer.write("  \"frameIndex\": " + snapshot.getFrameIndex() + "\n");
            writer.write("}\n");
        } catch (IOException e) {
            plugin.getLogger().warning("Failed to write screen_quadrant_request.json: " + e.getMessage());
        } finally {
            if (writer != null) {
                try { writer.close(); } catch (IOException ignored) {}
            }
        }
    }

    private String safe(String input) {
        if (input == null) {
            return "";
        }
        return input.replace("\"", "\\\"");
    }
}
EOF

echo "✔ QuadrantFrameExporter.java written"

########################################################################
# 11) Main.java — wire up commands
########################################################################

cat << 'EOF' > "${SRC_MAIN}/Main.java"
package com.lukesky;

import org.bukkit.plugin.java.JavaPlugin;

public final class Main extends JavaPlugin {

    @Override
    public void onEnable() {
        getLogger().info("==============================================");
        getLogger().info("  SkyLighting — 8XD Quadrant Frame Ping (L3) ");
        getLogger().info("  • Omega scalar (digit reversal)             ");
        getLogger().info("  • LIGHT / SHADE / COLOR quadrant modes      ");
        getLogger().info("  • /skyres client resolution ping            ");
        getLogger().info("  • /skyframe explicit frame ping             ");
        getLogger().info("==============================================");

        if (getCommand("skyomega") != null) {
            getCommand("skyomega").setExecutor(new OmegaDebugCommand(this));
        } else {
            getLogger().warning("Command /skyomega missing from plugin.yml!");
        }

        if (getCommand("skyquad") != null) {
            getCommand("skyquad").setExecutor(new QuadrantDebugCommand(this));
        } else {
            getLogger().warning("Command /skyquad missing from plugin.yml!");
        }

        if (getCommand("skyres") != null) {
            getCommand("skyres").setExecutor(new ScreenResolutionCommand(this));
        } else {
            getLogger().warning("Command /skyres missing from plugin.yml!");
        }

        if (getCommand("skyframe") != null) {
            getCommand("skyframe").setExecutor(new QuadrantFrameExporter(this));
        } else {
            getLogger().warning("Command /skyframe missing from plugin.yml!");
        }
    }

    @Override
    public void onDisable() {
        getLogger().info("SkyLighting shutting down — quadrants fold, frames rest.");
    }
}
EOF

echo "✔ Main.java written"

########################################################################
# 12) screen_quadrant_mapper.py — quarter grid using 2-way ping
########################################################################

cat << 'EOF' > "${SKY_ROOT}/screen_quadrant_mapper.py"
#!/usr/bin/env python3
"""
screen_quadrant_mapper.py — 8XD quadrant frame ping mapper (Layer 3).

Focus:

  • Read player_resolution.json:
       { "width": W, "height": H, "frameIndex": ... }
  • Read screen_quadrant_request.json:
       { "player": "...", "uuid": "...", "width": W, "height": H, "frameIndex": N }
  • Compute only a quarter grid for TOP_LEFT (base tile).
  • Define 4 quadrants with 3 modes: LIGHT, SHADE, COLOR.
  • Dump screen_quadrant_layout.json for Java + NumPy.

We still only compute 1/4 of the pixel count per frame (conceptually):
  - quarter width  = W / 2
  - quarter height = H / 2

The remaining 3 quadrants mirror or transform this base tile logically.
"""

import json
import os
from typing import Dict, Any

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
PLAYER_RES_JSON = os.path.join(ROOT, "..", "player_resolution.json")
REQ_JSON = os.path.join(ROOT, "..", "screen_quadrant_request.json")
OUT_JSON = os.path.join(ROOT, "screen_quadrant_layout.json")


def load_json(path: str, default: Dict[str, Any]) -> Dict[str, Any]:
    if os.path.isfile(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def load_resolution() -> Dict[str, Any]:
    return load_json(
        PLAYER_RES_JSON,
        {"width": 1920, "height": 1080, "frameIndex": 0},
    )


def load_request() -> Dict[str, Any]:
    return load_json(
        REQ_JSON,
        {"player": "Unknown", "uuid": "", "width": 1920, "height": 1080, "frameIndex": 0},
    )


def compute_quarter_grid(width: int, height: int) -> Dict[str, Any]:
    q_width = max(1, width // 2)
    q_height = max(1, height // 2)

    u = np.linspace(0.0, 0.5, num=q_width, endpoint=False, dtype=np.float64)
    v = np.linspace(0.0, 0.5, num=q_height, endpoint=False, dtype=np.float64)

    uu, vv = np.meshgrid(u, v)

    base_tile = {
        "width": int(q_width),
        "height": int(q_height),
        "u_min": float(u.min()),
        "u_max": float(u.max()),
        "v_min": float(v.min()),
        "v_max": float(v.max()),
        "sample_count": int(uu.size),
    }
    return base_tile


def build_layout(res: Dict[str, Any], req: Dict[str, Any]) -> Dict[str, Any]:
    width = int(res.get("width", 1920))
    height = int(res.get("height", 1080))

    frame_index = int(req.get("frameIndex", 0))
    player = str(req.get("player", "Unknown"))
    uuid = str(req.get("uuid", ""))

    quarter = compute_quarter_grid(width, height)

    layout = {
        "resolution": {"width": width, "height": height},
        "frameIndex": frame_index,
        "player": player,
        "uuid": uuid,
        "quarter": quarter,
        "quadrants": {
            "TOP_LEFT": {
                "mode": "LIGHT",
                "u_range": [0.0, 0.5],
                "v_range": [0.0, 0.5],
            },
            "TOP_RIGHT": {
                "mode": "SHADE",
                "u_range": [0.5, 1.0],
                "v_range": [0.0, 0.5],
            },
            "BOTTOM_LEFT": {
                "mode": "COLOR",
                "u_range": [0.0, 0.5],
                "v_range": [0.5, 1.0],
            },
            "BOTTOM_RIGHT": {
                "mode": "COLOR",
                "u_range": [0.5, 1.0],
                "v_range": [0.5, 1.0],
            },
        },
    }
    return layout


def main() -> None:
    res = load_resolution()
    req = load_request()
    layout = build_layout(res, req)

    with open(OUT_JSON, "w") as f:
        json.dump(layout, f, indent=2)

    print("8XD screen quadrant layout written:")
    print("  Path   :", OUT_JSON)
    print("  Player :", layout.get("player"), layout.get("uuid"))
    print("  Res    :", layout["resolution"]["width"], "x", layout["resolution"]["height"])
    q = layout["quarter"]
    print("  1/4    :", q["width"], "x", q["height"], "samples:", q["sample_count"])
    print("  Frame  :", layout["frameIndex"])
    print("Quadrant modes: LIGHT (TL), SHADE (TR), COLOR (BL/BR).")


if __name__ == "__main__":
    main()
EOF

chmod +x "${SKY_ROOT}/screen_quadrant_mapper.py"
echo "✔ screen_quadrant_mapper.py written"

########################################################################
# 13) screen_colormap_generator.py — LIGHT/SHADE/COLOR 4-checker maps
########################################################################

cat << 'EOF' > "${SKY_ROOT}/screen_colormap_generator.py"
#!/usr/bin/env python3
"""
screen_colormap_generator.py — 8XD LIGHT/SHADE/COLOR checker colormaps.

Focus:

  • Read screen_quadrant_layout.json (from screen_quadrant_mapper.py).
  • Build a quarter-tile color field in NumPy:
       - base_color   : a soft gradient in 0–1
       - light_map    : white + color 4-checker
       - shade_map    : black + color 4-checker
       - color_map    : pure color
  • Write screen_colormap_8xd.json with 0–1 floats only.

Quarter tile concept:
  We only compute a Wq × Hq tile for TOP_LEFT. The other three quadrants
  are logical transforms / mirrors of this tile. That keeps total pixel
  computations to 1/4 per frame.
"""

import json
import os
from typing import Dict, Any

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
LAYOUT_JSON = os.path.join(ROOT, "screen_quadrant_layout.json")
OUT_JSON = os.path.join(ROOT, "screen_colormap_8xd.json")


def load_layout() -> Dict[str, Any]:
    if not os.path.isfile(LAYOUT_JSON):
        raise FileNotFoundError(
            "screen_quadrant_layout.json is missing. "
            "Run screen_quadrant_mapper.py first."
        )
    with open(LAYOUT_JSON, "r") as f:
        return json.load(f)


def build_colormaps(layout: Dict[str, Any]) -> Dict[str, Any]:
    q_info = layout["quarter"]
    wq = int(q_info["width"])
    hq = int(q_info["height"])
    frame_index = int(layout.get("frameIndex", 0))

    u = np.linspace(0.0, 0.5, num=wq, endpoint=False, dtype=np.float64)
    v = np.linspace(0.0, 0.5, num=hq, endpoint=False, dtype=np.float64)
    uu, vv = np.meshgrid(u, v)

    center_u = 0.25
    center_v = 0.25
    dist = np.sqrt((uu - center_u) ** 2 + (vv - center_v) ** 2)
    dist_norm = dist / np.max(dist) if np.max(dist) > 0 else dist

    phase = (frame_index % 64) / 64.0
    base_color = np.clip(1.0 - dist_norm + 0.25 * np.sin(2.0 * np.pi * phase), 0.0, 1.0)

    rows = np.arange(hq).reshape(-1, 1)
    cols = np.arange(wq).reshape(1, -1)
    checker = (rows % 2) ^ (cols % 2)
    checker_f = checker.astype(np.float64)

    light_white = 1.0
    light_color_weight = 0.85
    light_white_weight = 0.35

    light_map = np.where(
        checker == 0,
        light_white * light_white_weight + base_color * (1.0 - light_white_weight),
        base_color * light_color_weight + (1.0 - light_color_weight) * 0.9,
    )
    light_map = np.clip(light_map, 0.0, 1.0)

    shade_color_weight = 0.6

    shade_map = np.where(
        checker == 0,
        base_color * 0.25,
        base_color * shade_color_weight + (1.0 - shade_color_weight) * 0.4,
    )
    shade_map = np.clip(shade_map, 0.0, 1.0)

    color_map = base_color.copy()

    def compress(arr: np.ndarray):
        return arr.astype(float).tolist()

    colormaps = {
        "meta": {
            "width_quarter": wq,
            "height_quarter": hq,
            "frameIndex": frame_index,
            "note": "Values 0–1 only. Quarter tile mirrored to 4 quadrants; "
                    "LIGHT / SHADE / COLOR applied per quadrant.",
        },
        "checker": compress(checker_f),
        "LIGHT": compress(light_map),
        "SHADE": compress(shade_map),
        "COLOR": compress(color_map),
    }
    return colormaps


def main() -> None:
    layout = load_layout()
    colormaps = build_colormaps(layout)
    with open(OUT_JSON, "w") as f:
        json.dump(colormaps, f, indent=2)
    print("8XD screen colormaps written:")
    print("  Path :", OUT_JSON)
    print("  Quarter size:",
          colormaps["meta"]["width_quarter"],
          "x",
          colormaps["meta"]["height_quarter"])
    print("  Frame:", colormaps["meta"]["frameIndex"])
    print("LIGHT / SHADE / COLOR checker maps ready.")


if __name__ == "__main__":
    main()
EOF

chmod +x "${SKY_ROOT}/screen_colormap_generator.py"
echo "✔ screen_colormap_generator.py written"

########################################################################
# 14) quadrant_channel_splitter.py — split LIGHT/SHADE/COLOR
########################################################################

cat << 'EOF' > "${SKY_ROOT}/quadrant_channel_splitter.py"
#!/usr/bin/env python3
"""
quadrant_channel_splitter.py — split LIGHT/SHADE/COLOR channels.

Focus:

  • Read screen_colormap_8xd.json:
       {
         "meta": { ... },
         "checker": [...],
         "LIGHT": [...],
         "SHADE": [...],
         "COLOR": [...]
       }
  • Write three separate JSON files:
       light_quarter_8xd.json
       shade_quarter_8xd.json
       color_quarter_8xd.json
    each containing only:
       {
         "width_quarter": ...,
         "height_quarter": ...,
         "frameIndex": ...,
         "data": [ [0..1], ... ]
       }

This makes it easy for any further processing layer to treat LIGHT/SHADE/COLOR
as distinct 0–1 fields, while still only touching 1/4 of the pixel grid.
"""

import json
import os
from typing import Dict, Any

ROOT = os.path.dirname(os.path.abspath(__file__))
IN_JSON = os.path.join(ROOT, "screen_colormap_8xd.json")
LIGHT_JSON = os.path.join(ROOT, "light_quarter_8xd.json")
SHADE_JSON = os.path.join(ROOT, "shade_quarter_8xd.json")
COLOR_JSON = os.path.join(ROOT, "color_quarter_8xd.json")


def load_colormaps() -> Dict[str, Any]:
    if not os.path.isfile(IN_JSON):
        raise FileNotFoundError(
            "screen_colormap_8xd.json is missing. "
            "Run screen_colormap_generator.py first."
        )
    with open(IN_JSON, "r") as f:
        return json.load(f)


def write_channel(meta: Dict[str, Any], data, out_path: str, label: str) -> None:
    payload = {
        "width_quarter": meta["width_quarter"],
        "height_quarter": meta["height_quarter"],
        "frameIndex": meta["frameIndex"],
        "channel": label,
        "data": data,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    maps = load_colormaps()
    meta = maps["meta"]
    light = maps["LIGHT"]
    shade = maps["SHADE"]
    color = maps["COLOR"]

    write_channel(meta, light, LIGHT_JSON, "LIGHT")
    write_channel(meta, shade, SHADE_JSON, "SHADE")
    write_channel(meta, color, COLOR_JSON, "COLOR")

    print("8XD quadrant channels split:")
    print("  LIGHT →", LIGHT_JSON)
    print("  SHADE →", SHADE_JSON)
    print("  COLOR →", COLOR_JSON)
    print("Quarter size:",
          meta["width_quarter"],
          "x",
          meta["height_quarter"],
          "frame", meta["frameIndex"])


if __name__ == "__main__":
    main()
EOF

chmod +x "${SKY_ROOT}/quadrant_channel_splitter.py"
echo "✔ quadrant_channel_splitter.py written"

########################################################################
# 15) Summary
########################################################################

echo
echo "-------------------------------------------------------"
echo "  QUADRANT FRAME PING • LAYER 3 COMPLETE"
echo "-------------------------------------------------------"
echo "Updated / created:"
echo "  • ${SKY_ROOT}/pom.xml"
echo "  • ${RES_MAIN}/plugin.yml"
echo "  • ${SRC_MAIN}/NumpyCoordBridge.java"
echo "  • ${SRC_MAIN}/OmegaMirrorField.java"
echo "  • ${SRC_MAIN}/ScreenQuadrantLayout.java"
echo "  • ${SRC_MAIN}/ResolutionState.java"
echo "  • ${SRC_MAIN}/ScreenResolutionCommand.java"
echo "  • ${SRC_MAIN}/OmegaDebugCommand.java"
echo "  • ${SRC_MAIN}/QuadrantDebugCommand.java"
echo "  • ${SRC_MAIN}/QuadrantFrameExporter.java"
echo "  • ${SRC_MAIN}/Main.java"
echo "  • ${SKY_ROOT}/screen_quadrant_mapper.py"
echo "  • ${SKY_ROOT}/screen_colormap_generator.py"
echo "  • ${SKY_ROOT}/quadrant_channel_splitter.py"
echo
echo "Concept flow (this layer):"
echo "  • /skyres <w> <h> → player_resolution.json (1-way ping up)."
echo "  • /skyframe      → screen_quadrant_request.json (frame ping up)."
echo "  • screen_quadrant_mapper.py → screen_quadrant_layout.json (1/4 grid)."
echo "  • screen_colormap_generator.py → screen_colormap_8xd.json (LIGHT/SHADE/COLOR)."
echo "  • quadrant_channel_splitter.py → light/shade/color_quarter_8xd.json."
echo
echo "Everything still respects:"
echo "  • 4 quadrants"
echo "  • 1/4 pixel count per frame"
echo "  • 3 map types: LIGHT, SHADE, COLOR."
echo "-------------------------------------------------------"
