package com.lukesky;

import org.bukkit.map.MapCanvas;
import org.bukkit.map.MapRenderer;
import org.bukkit.map.MapView;
import org.bukkit.entity.Player;

import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.image.BufferedImage;

public class ImageMapRenderer extends MapRenderer {

    private final BufferedImage source;
    private boolean rendered = false;

    public ImageMapRenderer(BufferedImage src) {
        super(false);
        this.source = scaleToMap(src);
    }

    private BufferedImage scaleToMap(BufferedImage original) {
        Image scaled = original.getScaledInstance(128, 128, Image.SCALE_SMOOTH);
        BufferedImage out = new BufferedImage(128, 128, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = out.createGraphics();
        g.drawImage(scaled, 0, 0, null);
        g.dispose();
        return out;
    }

    @Override
    public void render(MapView map, MapCanvas canvas, Player player) {
        if (rendered) return;
        for (int x = 0; x < 128; x++) {
            for (int y = 0; y < 128; y++) {
                int rgb = source.getRGB(x, y);
                byte mcColor = MapColorUtil.rgbToMapColor(rgb);
                canvas.setPixel(x, y, mcColor);
            }
        }
        rendered = true;
    }
}
