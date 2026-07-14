#!/usr/bin/env python3
"""Session hooks for Command Center — JSON-safe parsing, no grep/sed."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CC_DIR = Path.home() / ".command-center"
CONTEXT_FILE = CC_DIR / "cc-context.json"
STATE_FILE = CC_DIR / "session-state.json"
PROFILE_FILE = CC_DIR / "profile.json"
TODOS_FILE = CC_DIR / "todos.md"
PR_DETECT_FILE = CC_DIR / "cc-last-pr.txt"
DEBUG_LOG = CC_DIR / "logs" / "session-debug.log"


def log_debug(message: str) -> None:
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with DEBUG_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {message}\n")


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else (default or {})
    except (json.JSONDecodeError, OSError) as exc:
        log_debug(f"read_json failed {path}: {exc}")
        return default or {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def parse_iso_timestamp(raw: str) -> datetime | None:
    if not raw:
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError as exc:
        log_debug(f"parse_iso_timestamp failed for {raw!r}: {exc}")
        return None


def idle_hours_since(raw: str) -> int:
    parsed = parse_iso_timestamp(raw)
    if not parsed:
        return 0
    delta = datetime.now(timezone.utc) - parsed
    return max(0, int(delta.total_seconds() // 3600))


def time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def count_todos() -> dict[str, int]:
    counts = {"pending": 0, "in_progress": 0, "done": 0}
    if not TODOS_FILE.exists():
        return counts
    section = ""
    for line in TODOS_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## In Progress"):
            section = "in_progress"
        elif line.startswith("## Pending"):
            section = "pending"
        elif line.startswith("## Done"):
            section = "done"
        elif line.startswith("## "):
            section = ""
        elif line.strip().startswith("- [") and section in counts:
            counts[section] += 1
    return counts


def detect_workspace(cwd: Path) -> tuple[str, str, int]:
    state = read_json(STATE_FILE)
    last_workspace = str(state.get("lastWorkspace") or "")
    contexts = CC_DIR / "contexts"
    if not contexts.is_dir():
        return "", last_workspace, 0

    matches: list[str] = []
    cwd_s = str(cwd.resolve())
    for repos_file in sorted(contexts.glob("*.repos")):
        ws_name = repos_file.stem
        text = repos_file.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "|" not in line:
                continue
            repo_path = line.split("|", 1)[1].strip()
            if not repo_path:
                continue
            repo_path = str(Path(repo_path).resolve())
            if cwd_s == repo_path or cwd_s.startswith(repo_path + "/"):
                matches.append(ws_name)
                break

    all_count = len(list(contexts.glob("*.repos")))
    if len(matches) == 1:
        return matches[0], last_workspace, all_count
    if len(matches) > 1:
        log_debug(
            f"detect_workspace: multiple workspaces match {cwd_s!r}: {matches} — using first. "
            "Check ~/.command-center/contexts/ for duplicate repo paths."
        )
        return matches[0], last_workspace, all_count

    all_ws = list(contexts.glob("*.repos"))
    if len(all_ws) == 1:
        return all_ws[0].stem, last_workspace, 1
    return last_workspace, last_workspace, len(all_ws)


def session_start(cwd: Path) -> None:
    CC_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_json(PROFILE_FILE)
    state = read_json(STATE_FILE)

    user_name = str(profile.get("name") or "")
    work_week = str(profile.get("workWeek") or "mon-fri") or "mon-fri"

    last_end = str(state.get("lastSessionEnd") or "")
    last_start = str(state.get("lastSessionStart") or "")
    last_timestamp = last_end or last_start
    idle_hours = idle_hours_since(last_timestamp)

    todos = count_todos()
    workspace, last_workspace, _ = detect_workspace(cwd)

    last_date = ""
    parsed_last = parse_iso_timestamp(last_timestamp)
    if parsed_last:
        last_date = parsed_last.astimezone().strftime("%Y-%m-%d")
    today_date = datetime.now().strftime("%Y-%m-%d")
    is_new_day = bool(last_date and last_date != today_date)

    day_of_week = datetime.now().isoweekday()  # Mon=1 ... Sun=7
    if work_week == "sun-thu":
        is_start_of_week = is_new_day and day_of_week == 7
    else:
        is_start_of_week = is_new_day and day_of_week == 1

    (CC_DIR / "standups").mkdir(parents=True, exist_ok=True)

    context = {
        "workspace": workspace,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_history": str(CC_DIR / "task-history" / workspace) if workspace else "",
        "docs": str(CC_DIR / "docs" / workspace) if workspace else "",
        "userName": user_name,
        "profileExists": PROFILE_FILE.exists(),
        "idleHours": idle_hours,
        "timeOfDay": time_of_day(),
        "todosPending": todos["pending"],
        "todosInProgress": todos["in_progress"],
        "todosDone": todos["done"],
        "lastWorkspace": last_workspace,
        "isNewDay": is_new_day,
        "isStartOfWeek": is_start_of_week,
        "workWeek": work_week,
        "missionsEnabled": (CC_DIR / "roles").is_dir() and any((CC_DIR / "roles").glob("*.md")),
    }
    write_json(CONTEXT_FILE, context)

    current_state_workspace = workspace or last_workspace
    write_json(
        STATE_FILE,
        {
            "lastSessionStart": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lastWorkspace": current_state_workspace,
            **({"lastSessionEnd": last_end} if last_end else {}),
        },
    )


def session_end() -> None:
    CC_DIR.mkdir(parents=True, exist_ok=True)
    context = read_json(CONTEXT_FILE)
    state = read_json(STATE_FILE)
    workspace = str(context.get("workspace") or "")
    last_session_start = str(state.get("lastSessionStart") or "")

    write_json(
        STATE_FILE,
        {
            "lastSessionEnd": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lastSessionStart": last_session_start,
            "lastWorkspace": workspace,
        },
    )

    if PR_DETECT_FILE.exists():
        PR_DETECT_FILE.unlink(missing_ok=True)


def capture_pr_url(output: str) -> None:
    import re

    found = re.findall(r"https://github.com/\S+/pull/\d+", output)
    if not found:
        return
    CC_DIR.mkdir(parents=True, exist_ok=True)
    existing: list[str] = []
    if PR_DETECT_FILE.exists():
        try:
            existing = json.loads(PR_DETECT_FILE.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = [existing] if existing else []
        except (json.JSONDecodeError, OSError):
            existing = []
    merged = existing + [u for u in found if u not in existing]
    PR_DETECT_FILE.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "start":
        session_start(Path.cwd())
        return 0
    if cmd == "end":
        session_end()
        return 0
    if cmd == "capture-pr":
        capture_pr_url(sys.stdin.read())
        return 0
    print(f"Usage: {sys.argv[0]} start|end|capture-pr", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
