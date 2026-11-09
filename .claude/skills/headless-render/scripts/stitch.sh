#!/usr/bin/env bash
# Stitch rendered frames into an MP4.
# Usage: bash stitch.sh <frames_dir> <out.mp4> [fps=30] [audio.wav]
# Frames must be named f_0001.png, f_0002.png ... (scene_template.py does this).
set -euo pipefail
DIR="$1"; OUT="$2"; FPS="${3:-30}"; AUDIO="${4:-}"
command -v ffmpeg >/dev/null || { echo "ffmpeg not found (macOS: brew install ffmpeg)" >&2; exit 1; }

FIRST=$(ls "$DIR"/f_*.png | head -1 | sed -E 's/.*f_0*([0-9]+)\.png/\1/')
ARGS=(-y -framerate "$FPS" -start_number "$FIRST" -i "$DIR/f_%04d.png")
if [ -n "$AUDIO" ]; then ARGS+=(-i "$AUDIO" -c:a aac -b:a 192k -shortest); fi
ARGS+=(-c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -movflags +faststart "$OUT")
ffmpeg -loglevel error "${ARGS[@]}"
echo "wrote $OUT"
