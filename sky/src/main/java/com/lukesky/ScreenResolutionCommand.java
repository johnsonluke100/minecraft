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
