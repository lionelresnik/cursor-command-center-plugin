#!/usr/bin/env bash
# Copy mission/dashboard tooling into ~/.command-center for hooks and offline use.
set -euo pipefail
CC_DIR="${HOME}/.command-center"
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$CC_DIR"/{roles,crews,missions,dashboard,scripts}

for f in "$PLUGIN_ROOT/templates/roles/"*.md; do
  [ -f "$f" ] || continue
  base="$(basename "$f")"
  [ -f "$CC_DIR/roles/$base" ] || cp "$f" "$CC_DIR/roles/$base"
done

for f in "$PLUGIN_ROOT/templates/crews/"*.yaml; do
  [ -f "$f" ] || continue
  base="$(basename "$f")"
  [ -f "$CC_DIR/crews/$base" ] || cp "$f" "$CC_DIR/crews/$base"
done

cp "$PLUGIN_ROOT/scripts/generate-dashboard.py" "$CC_DIR/scripts/"
cp "$PLUGIN_ROOT/scripts/generate-dashboard.sh" "$CC_DIR/scripts/"
chmod +x "$CC_DIR/scripts/generate-dashboard.sh"
cp "$PLUGIN_ROOT/assets/dashboard-template.html" "$CC_DIR/dashboard/template.html"

echo "Installed mission tools under $CC_DIR"
