#!/usr/bin/env bash
# Remove demo missions seeded by seed-demo-missions.sh.
set -euo pipefail

CC_DIR="${HOME}/.command-center"
MARKER="$CC_DIR/demo-missions.json"
MISSIONS_DIR="$CC_DIR/missions"

removed=0

remove_mission() {
  local mid="$1"
  local dir="$MISSIONS_DIR/$mid"
  if [ -d "$dir" ]; then
    rm -rf "$dir"
    removed=$((removed + 1))
    echo "  removed $mid"
  fi
}

if [ -f "$MARKER" ]; then
  while IFS= read -r mid; do
    [ -n "$mid" ] || continue
    remove_mission "$mid"
  done < <(MARKER="$MARKER" python3 - <<'PY'
import json, os
from pathlib import Path
data = json.loads(Path(os.environ["MARKER"]).read_text())
for mid in data.get("missionIds", []):
    print(mid)
PY
)
  rm -f "$MARKER"
fi

if [ -d "$MISSIONS_DIR" ]; then
  for dir in "$MISSIONS_DIR"/demo-*; do
    [ -d "$dir" ] || continue
    remove_mission "$(basename "$dir")"
  done
  for dir in "$MISSIONS_DIR"/*; do
    [ -d "$dir" ] || continue
    mid="$(basename "$dir")"
    mf="$dir/mission.json"
    if [ -f "$mf" ] && python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('demo') else 1)" "$mf" 2>/dev/null; then
      remove_mission "$mid"
    fi
  done
fi

if [ -x "$CC_DIR/scripts/generate-dashboard.sh" ]; then
  "$CC_DIR/scripts/generate-dashboard.sh" 2>/dev/null || true
fi

echo "Removed $removed demo mission(s). Roles, crews, and real missions were kept."
