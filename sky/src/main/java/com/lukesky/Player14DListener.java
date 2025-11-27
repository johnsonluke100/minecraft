package com.lukesky;

import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;

public class Player14DListener implements Listener {

    private final Main plugin;

    public Player14DListener(Main plugin) {
        this.plugin = plugin;
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent e) {
        Player p = e.getPlayer();
        String id = p.getUniqueId().toString();
        if (!HypercubeRegistry.hasPlayer(id)) {
            HypercubeRegistry.initPlayer(id);
        }
        p.sendMessage("§b[8XD] §7Your 14-axis continuum is now bonded to your movement.");
    }

    @EventHandler
    public void onMove(PlayerMoveEvent e) {
        Player p = e.getPlayer();
        String id = p.getUniqueId().toString();
        if (!HypercubeRegistry.hasPlayer(id)) {
            HypercubeRegistry.initPlayer(id);
        }
        double[] prev = HypercubeRegistry.getAxes(id);
        double[] mapped = ContinuumMapper.map(p, prev);
        HypercubeRegistry.setAxes(id, mapped);
    }
}
