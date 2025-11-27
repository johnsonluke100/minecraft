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
