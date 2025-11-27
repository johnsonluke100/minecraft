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
