package com.lukesky;

import org.bukkit.GameMode;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;
import org.bukkit.Location;

/**
 * ExtendedReachListener
 *
 * First layer of the new geometry: lets players break blocks up to
 * 8 blocks away via raycasting, without client mods.
 *
 * This keeps vanilla XYZ for control, but allows the "field of force"
 * around the player to extend.
 */
public class ExtendedReachListener implements Listener {

    // Max reach distance in blocks
    private static final double MAX_REACH = 8.0;

    // Step size for ray marching (smaller = more precise)
    private static final double STEP = 0.2;

    @EventHandler
    public void onPlayerInteract(PlayerInteractEvent event) {
        Action action = event.getAction();

        if (action != Action.LEFT_CLICK_AIR && action != Action.LEFT_CLICK_BLOCK) {
            return;
        }

        Player player = event.getPlayer();

        if (player.getGameMode() == GameMode.SPECTATOR) {
            return;
        }

        Block target = raycastFirstSolidBlock(player, MAX_REACH);
        if (target == null) {
            return;
        }

        if (isUnbreakable(target.getType())) {
            return;
        }

        event.setCancelled(true);

        ItemStack inHand = player.getItemInHand();
        if (inHand != null && inHand.getType() != Material.AIR) {
            target.breakNaturally(inHand);
        } else {
            target.setType(Material.AIR);
        }
    }

    private boolean isUnbreakable(Material type) {
        if (type == Material.BEDROCK) {
            return true;
        }
        return false;
    }

    private Block raycastFirstSolidBlock(Player player, double maxDistance) {
        Location eye = player.getEyeLocation().clone();
        Vector dir = eye.getDirection().normalize();

        double traveled = 0.0;

        while (traveled <= maxDistance) {
            Location current = eye.clone().add(dir.clone().multiply(traveled));
            Block block = current.getBlock();

            if (block != null && block.getType() != Material.AIR) {
                return block;
            }
            traveled += STEP;
        }

        return null;
    }
}
