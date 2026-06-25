#!/usr/bin/env bash
# Run ON eshwar-serv-gpu-01 (GPU server), not on your Mac.
# Fixes: systemd ollama (User=ollama) cannot use /home/eshwar/ollama-models
#
# Default: in-place fix (chown + home traverse) — NO 24GB copy.
# Relocate only when OLLAMA_MODELS_TARGET is set and has free space (e.g. /srv/ollama-models).
#
#   bash gpu-ollama-fix-server.sh
#   OLLAMA_MODELS_TARGET=/srv/ollama-models bash gpu-ollama-fix-server.sh   # move, not copy twice
#
# Requires sudo for systemd.

set -euo pipefail

OVERRIDE="/etc/systemd/system/ollama.service.d/override.conf"
EXISTING_HOME="/home/eshwar/ollama-models"
MODE="${OLLAMA_FIX_MODE:-inplace}"  # inplace | relocate
TARGET="${OLLAMA_MODELS_TARGET:-}"

echo "=== Disk ==="
df -h / /var /home /srv 2>/dev/null || df -h

echo ""
echo "=== Ollama service (before) ==="
systemctl is-active ollama || true
curl -s --max-time 5 http://localhost:11434/api/tags || echo "(api/tags failed)"

echo ""
echo "=== Current systemd config ==="
systemctl show ollama -p User,Group,Environment 2>/dev/null || true
if [[ -f "$OVERRIDE" ]]; then
  echo "--- $OVERRIDE ---"
  sudo cat "$OVERRIDE"
fi

echo ""
echo "=== Model blob dirs ==="
for d in \
  "$EXISTING_HOME" \
  "/home/eshwar/.ollama/models" \
  "/srv/ollama-models" \
  "/var/lib/ollama/models"; do
  if [[ -d "$d" ]]; then
    echo "  $d — $(sudo du -sh "$d" 2>/dev/null | cut -f1) — $(sudo find "$d" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ') entries"
  fi
done

# Find where blobs actually live
SRC=""
for candidate in "$EXISTING_HOME" "/home/eshwar/.ollama/models" "/srv/ollama-models"; do
  if [[ -d "$candidate" ]] && [[ -n "$(sudo ls -A "$candidate" 2>/dev/null)" ]]; then
    SRC="$candidate"
    break
  fi
done

if [[ -z "$SRC" ]]; then
  SRC="${TARGET:-/var/lib/ollama/models}"
  echo ""
  echo "No model blobs found — will use empty dir: $SRC"
  sudo mkdir -p "$SRC"
  sudo chown ollama:ollama "$SRC"
  MODELS_DIR="$SRC"
elif [[ "$MODE" == "relocate" && -n "$TARGET" && "$TARGET" != "$SRC" ]]; then
  echo ""
  echo "=== Relocate $SRC → $TARGET (mv, not copy) ==="
  need_k="$(sudo du -sk "$SRC" | cut -f1)"
  avail_k="$(df -k "$(dirname "$TARGET")" | awk 'NR==2 {print $4}')"
  if [[ "$avail_k" -lt "$need_k" ]]; then
    echo "ERROR: need ~$((need_k / 1024 / 1024))G free under $(dirname "$TARGET"), have ~$((avail_k / 1024 / 1024))G"
    exit 1
  fi
  sudo mkdir -p "$TARGET"
  sudo rsync -a --remove-source-files "$SRC/" "$TARGET/" || sudo mv "$SRC"/* "$TARGET/"
  sudo rmdir "$SRC" 2>/dev/null || true
  sudo chown -R ollama:ollama "$TARGET"
  MODELS_DIR="$TARGET"
else
  echo ""
  echo "=== In-place fix on $SRC (no copy) ==="
  MODELS_DIR="$SRC"
  # ollama user must traverse /home/eshwar to reach ollama-models
  if [[ "$MODELS_DIR" == /home/eshwar/* ]]; then
    echo "Ensuring /home/eshwar is traversable by ollama…"
    chmod o+x /home/eshwar
  fi
  sudo chown -R ollama:ollama "$MODELS_DIR"
  sudo chmod 755 "$MODELS_DIR"
fi

echo ""
echo "=== Writing systemd override → OLLAMA_MODELS=$MODELS_DIR ==="
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee "$OVERRIDE" >/dev/null <<EOF
[Service]
Environment="OLLAMA_MODELS=$MODELS_DIR"
EOF

sudo systemctl daemon-reload
sudo systemctl restart ollama
sleep 2

echo ""
echo "=== Ollama service (after) ==="
systemctl is-active ollama
systemctl show ollama -p User,Environment

echo ""
echo "=== api/tags ==="
TAGS=$(curl -s --max-time 15 http://localhost:11434/api/tags)
echo "$TAGS" | head -c 800
echo ""

if echo "$TAGS" | grep -q '"models"'; then
  echo ""
  echo "OK — server Ollama is healthy."
  echo "On your Mac (local Ollama stopped):"
  echo "  ssh -N -L 127.0.0.1:11500:127.0.0.1:11434 eshwar@eshwar-serv-gpu-01.cs.illinois.edu"
  echo "  curl -s http://127.0.0.1:11500/api/tags"
  echo ""
  echo "Optional — pull MoE candidate:"
  echo "  ollama pull qwen3:30b-a3b-instruct-2507-q4_K_M"
else
  echo ""
  echo "Still failing. Check: journalctl -u ollama -n 30 --no-pager"
  exit 1
fi
