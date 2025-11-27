#!/bin/bash
set -e

SKY_ROOT="$HOME/Desktop/sky"
SERVER_ROOT="$HOME/Desktop/godmode"
JAR_SOURCE="$SKY_ROOT/target/SkyLighting-1.0-SNAPSHOT.jar"
PLUGIN_DEST="$SERVER_ROOT/plugins/SkyLighting.jar"

echo
echo "---------------------------------------------"
echo "     MINECRAFT 8XD — CONTINUUM GODMODE v6"
echo "---------------------------------------------"
echo "Sky project : $SKY_ROOT"
echo "Server root : $SERVER_ROOT"
echo "Plugin jar  : $JAR_SOURCE"
echo "Mic engine  : $SKY_ROOT/8xd_mic_engine.command"
echo "JSON field  : $SKY_ROOT/bpm_sync.json"
echo

echo "Building SkyLighting plugin..."
cd "$SKY_ROOT"
mvn -q clean package

mkdir -p "$SERVER_ROOT/plugins"

rm -f "$SERVER_ROOT"/plugins/SkyLighting-*.jar 2>/dev/null || true
rm -f "$PLUGIN_DEST" 2>/dev/null || true

cp "$JAR_SOURCE" "$PLUGIN_DEST"
echo "✔ Plugin deployed to server/plugins/SkyLighting.jar"

ln -sf "$SKY_ROOT/bpm_sync.json" "$SERVER_ROOT/bpm_sync.json"
echo "✔ Harmonic JSON linked into server root"

MIC_CMD="$SKY_ROOT/8xd_mic_engine.command"
if [ -x "$MIC_CMD" ]; then
  echo
  echo "Starting 8XD PURE CONTINUUM mic/NumPy engine..."
  nohup "$MIC_CMD" >/dev/null 2>&1 &
  MIC_PID=$!
  echo "✔ Mic continuum engine running with PID $MIC_PID"
else
  echo "❌ Mic engine not found or not executable at $MIC_CMD"
fi

echo
echo "---------------------------------------------"
echo "        STARTING MINECRAFT SERVER"
echo "---------------------------------------------"
cd "$SERVER_ROOT"

if [ -f "paper.jar" ]; then
  java -Xms1G -Xmx2G -jar paper.jar nogui
else
  echo "❌ paper.jar not found in $SERVER_ROOT"
  exit 1
fi
