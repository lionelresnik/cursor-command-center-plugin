#!/usr/bin/env bash
# Detect PR URLs from shell output (after gh pr create / git push).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -t 0 ]; then
  python3 "$SCRIPT_DIR/cc_session.py" capture-pr
fi
