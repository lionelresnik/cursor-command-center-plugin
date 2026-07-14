#!/usr/bin/env bash
# Session start hook — delegates to cc_session.py for JSON-safe parsing.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/cc_session.py" start
