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
