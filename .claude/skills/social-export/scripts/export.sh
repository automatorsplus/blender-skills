#!/usr/bin/env bash
# Cut one 16:9 master into the formats each platform wants.
# Usage: bash export.sh <master.mp4> <out_dir> [crop|fill]
#   crop (default): centre crop. Right when the subject sits in the middle of the frame.
#   fill: the whole 16:9 shot sits in the middle, a blurred copy fills the rest. Right when the edges matter.
# For a vertical video that looks designed rather than cropped, re-render at 1080x1920 instead (see SKILL.md).
set -euo pipefail
IN="$1"; OUT="$2"; MODE="${3:-crop}"
mkdir -p "$OUT"
NAME=$(basename "$IN" .mp4)
ENC=(-c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -movflags +faststart -c:a copy)

# 16:9 for YouTube, LinkedIn and X
ffmpeg -loglevel error -y -i "$IN" -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" "${ENC[@]}" "$OUT/${NAME}-16x9.mp4"

if [ "$MODE" = "fill" ]; then
  V916="[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
  V11="[0:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,boxblur=30:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
  ffmpeg -loglevel error -y -i "$IN" -filter_complex "$V916" "${ENC[@]}" "$OUT/${NAME}-9x16.mp4"
  ffmpeg -loglevel error -y -i "$IN" -filter_complex "$V11" "${ENC[@]}" "$OUT/${NAME}-1x1.mp4"
else
  ffmpeg -loglevel error -y -i "$IN" -vf "scale=-2:1920,crop=1080:1920" "${ENC[@]}" "$OUT/${NAME}-9x16.mp4"
  ffmpeg -loglevel error -y -i "$IN" -vf "scale=-2:1080,crop=1080:1080" "${ENC[@]}" "$OUT/${NAME}-1x1.mp4"
fi

for f in "$OUT/${NAME}"-*.mp4; do
  size=$(du -m "$f" | cut -f1)
  dims=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$f")
  echo "$(basename "$f")  ${dims}  ${size}MB"
done
