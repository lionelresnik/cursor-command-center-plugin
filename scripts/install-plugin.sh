#!/usr/bin/env bash
# Install or update Command Center in Cursor's local plugins directory.
set -euo pipefail

# Temporarily disable unbound variable checking for safe fallback assignment
set +u
REPO="${COMMAND_CENTER_PLUGIN_REPO:-https://github.com/lionelresnik/cursor-command-center-plugin.git}"
PLUGIN_DIR="${CURSOR_PLUGIN_DIR:-$HOME/.cursor/plugins/local/command-center}"
set -u

echo "→ Command Center plugin → $PLUGIN_DIR"

mkdir -p "$(dirname "$PLUGIN_DIR")"

if [ -d "$PLUGIN_DIR/.git" ]; then
  echo "→ Updating existing clone…"
  git -C "$PLUGIN_DIR" fetch origin
  git -C "$PLUGIN_DIR" checkout main
  if ! git -C "$PLUGIN_DIR" pull --ff-only origin main 2>/dev/null; then
    echo "→ Local changes block update — resetting install to origin/main"
    echo "  (Your data in ~/.command-center/ is unchanged.)"
    git -C "$PLUGIN_DIR" reset --hard origin/main
    git -C "$PLUGIN_DIR" clean -fd
  fi
elif [ -d "$PLUGIN_DIR" ]; then
  echo "→ Backing up existing folder to ${PLUGIN_DIR}.bak.$(date +%Y%m%d%H%M%S)"
  mv "$PLUGIN_DIR" "${PLUGIN_DIR}.bak.$(date +%Y%m%d%H%M%S)"
  git clone "$REPO" "$PLUGIN_DIR"
else
  echo "→ Cloning from $REPO…"
  git clone "$REPO" "$PLUGIN_DIR"
fi

chmod +x "$PLUGIN_DIR"/scripts/*.sh 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/cc "$PLUGIN_DIR"/scripts/cc_session.py \
         "$PLUGIN_DIR"/scripts/cc_lock.py "$PLUGIN_DIR"/scripts/cc_todos.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/generate-dashboard.py 2>/dev/null || true

echo "→ Seeding mission roles, crews, and dashboard tools…"
"$PLUGIN_DIR/scripts/install-mission-tools.sh"

VERSION="$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$PLUGIN_DIR/.cursor-plugin/plugin.json" | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')"
echo ""
echo "✓ Installed command-center v${VERSION:-?}"
echo "✓ Seeded ~/.command-center/roles, crews, and dashboard scripts"
echo ""
echo "Next steps:"
echo "  1. Reload Cursor: Cmd+Shift+P → \"Developer: Reload Window\""
echo "  2. Enable the plugin: Cursor Settings → Plugins → command-center"
echo "  3. In chat: @lucius help"
echo "  4. Optional: @lu init demo missions (sample board data)"
echo ""
echo "Data stays in ~/.command-center/ (unchanged by plugin updates)."
