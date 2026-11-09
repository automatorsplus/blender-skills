#!/usr/bin/env bash
# Print the path to the Blender executable, or exit 1 with install advice.
# Usage: BLENDER=$(bash find_blender.sh)
set -u

if [ -n "${BLENDER:-}" ] && [ -x "$BLENDER" ]; then echo "$BLENDER"; exit 0; fi

candidates=(
  "/Applications/Blender.app/Contents/MacOS/Blender"
  "$HOME/Applications/Blender.app/Contents/MacOS/Blender"
  "/usr/bin/blender"
  "/usr/local/bin/blender"
  "/snap/bin/blender"
  "/c/Program Files/Blender Foundation/Blender/blender.exe"
)
# Windows installs put the version in the folder name, e.g. "Blender 4.4"
for d in "/c/Program Files/Blender Foundation"/Blender*/; do
  [ -d "$d" ] && candidates+=("${d}blender.exe")
done

if command -v blender >/dev/null 2>&1; then command -v blender; exit 0; fi
for c in "${candidates[@]}"; do
  if [ -x "$c" ]; then echo "$c"; exit 0; fi
done

echo "Blender not found. Install it free from https://www.blender.org/download/ (macOS: brew install --cask blender), or set BLENDER=/path/to/blender." >&2
exit 1
