#!/usr/bin/env bash
# Copy demo missions into ~/.command-center/missions/ for dashboard onboarding.
set -euo pipefail

CC_DIR="${HOME}/.command-center"
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_SRC="$PLUGIN_ROOT/templates/demo-missions"
MARKER="$CC_DIR/demo-missions.json"

if [ ! -f "$DEMO_SRC/manifest.json" ]; then
  echo "Error: demo templates missing at $DEMO_SRC" >&2
  exit 1
fi

"$PLUGIN_ROOT/scripts/install-mission-tools.sh"
mkdir -p "$CC_DIR/missions"

added=0
skipped=0

while IFS= read -r mid; do
  [ -n "$mid" ] || continue
  dest="$CC_DIR/missions/$mid"
  if [ -d "$dest" ]; then
    skipped=$((skipped + 1))
    continue
  fi
  cp -R "$DEMO_SRC/$mid" "$dest"
  added=$((added + 1))
done < <(DEMO_SRC="$DEMO_SRC" python3 - <<'PY'
import json, os
root = os.environ["DEMO_SRC"]
with open(os.path.join(root, "manifest.json")) as f:
    data = json.load(f)
for mid in data.get("missionIds", []):
    print(mid)
PY
)

DEMO_SRC="$DEMO_SRC" CC_DIR="$CC_DIR" python3 - <<'PY'
import json, os
from datetime import datetime, timezone
from pathlib import Path

cc = Path(os.environ["CC_DIR"])
demo_src = Path(os.environ["DEMO_SRC"])
manifest = json.loads((demo_src / "manifest.json").read_text())
payload = {
    "version": manifest.get("version", 1),
    "description": manifest.get("description", ""),
    "missionIds": manifest.get("missionIds", []),
    "seededAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
(cc / "demo-missions.json").write_text(json.dumps(payload, indent=2) + "\n")
PY

if [ -x "$CC_DIR/scripts/generate-dashboard.sh" ]; then
  "$CC_DIR/scripts/generate-dashboard.sh" 2>/dev/null || true
fi

echo "Demo missions: $added added, $skipped already present."
echo "Run lu dashboard to view. Remove anytime with lu remove demo missions."
