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
