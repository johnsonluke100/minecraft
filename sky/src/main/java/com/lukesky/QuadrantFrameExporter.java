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
