#!/usr/bin/env python3
"""Todo store for Command Center — JSON source of truth, markdown as a view.

Source of truth: ~/.command-center/todos.json
Human view:      ~/.command-center/todos.md (regenerated on every mutation)

The agent calls these commands instead of hand-editing markdown, so mutations
are atomic, cheap, and never drop or reorder items.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cc_lock import file_lock  # noqa: E402

CC_DIR = Path.home() / ".command-center"
TODOS_JSON = CC_DIR / "todos.json"
TODOS_MD = CC_DIR / "todos.md"
ARCHIVE_MD = CC_DIR / "todos-archive.md"

STATUSES = ("pending", "in_progress", "done")
PRIORITIES = ("high", "medium", "low")
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_store() -> dict:
    return {"version": 1, "nextId": 1, "todos": []}


def load_store() -> dict:
    if not TODOS_JSON.exists():
        # First run: migrate an existing markdown file if present.
        if TODOS_MD.exists():
            return migrate_from_markdown(TODOS_MD.read_text(encoding="utf-8"))
        return _empty_store()
    try:
        data = json.loads(TODOS_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_store()
    if not isinstance(data, dict) or "todos" not in data:
        return _empty_store()
    data.setdefault("version", 1)
    data.setdefault("nextId", max((t.get("id", 0) for t in data["todos"]), default=0) + 1)
    return data


def save_store(store: dict) -> None:
    CC_DIR.mkdir(parents=True, exist_ok=True)
    with file_lock("todos"):
        tmp = TODOS_JSON.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")
        tmp.replace(TODOS_JSON)
        TODOS_MD.write_text(render_markdown(store), encoding="utf-8")


# ---------------------------------------------------------------------------
# Migration from legacy todos.md
# ---------------------------------------------------------------------------

_LINE_RE = re.compile(r"^- \[([ xX])\]\s+(.*)$")
_WS_RE = re.compile(r"\*\*\[([^\]]+)\]\*\*")
_TICKET_RE = re.compile(r"`#([A-Z][A-Z0-9]+-\d+)`")
_PRIORITY_RE = re.compile(r"`?#?priority-(high|medium|low)`?", re.I)
_SOURCE_RE = re.compile(r"`#(user|lucius)`")
_DATE_RE = re.compile(r"_\(completed ([0-9]{4}-[0-9]{2}-[0-9]{2})\)_")


def migrate_from_markdown(text: str) -> dict:
    store = _empty_store()
    section = ""
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("## in progress"):
            section = "in_progress"
            continue
        if low.startswith("## pending"):
            section = "pending"
            continue
        if low.startswith("## done"):
            section = "done"
            continue
        if line.startswith("## "):
            section = ""
            continue
        m = _LINE_RE.match(line.strip())
        if not m or section not in STATUSES:
            continue
        checked, body = m.group(1), m.group(2)
        status = "done" if checked.lower() == "x" else section
        ws = _WS_RE.search(body)
        ticket = _TICKET_RE.search(body)
        prio = _PRIORITY_RE.search(body)
        source = _SOURCE_RE.search(body)
        completed = _DATE_RE.search(body)
        # Strip tags/markers to recover the plain text.
        text_only = body
        for rx in (_WS_RE, _TICKET_RE, _PRIORITY_RE, _SOURCE_RE, _DATE_RE):
            text_only = rx.sub("", text_only)
        text_only = re.sub(r"`[^`]*`", "", text_only)
        text_only = re.sub(r"~~([^~]*)~~", r"\1", text_only).strip(" -~")
        store["todos"].append(
            {
                "id": store["nextId"],
                "text": text_only.strip(),
                "workspace": ws.group(1) if ws else "",
                "status": status,
                "priority": (prio.group(1).lower() if prio else "medium"),
                "ticket": ticket.group(1) if ticket else None,
                "source": source.group(1) if source else "user",
                "createdAt": _now(),
                "completedAt": (completed.group(1) if completed else (_now() if status == "done" else None)),
            }
        )
        store["nextId"] += 1
    return store


# ---------------------------------------------------------------------------
# Markdown rendering (human view)
# ---------------------------------------------------------------------------

def _sorted(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda t: _PRIORITY_ORDER.get(t.get("priority", "medium"), 1))


def _fmt(t: dict) -> str:
    tags = [f"`#priority-{t['priority']}`"]
    if t.get("ticket"):
        tags.append(f"`#{t['ticket']}`")
    tags.append(f"`#{t.get('source', 'user')}`")
    ws = f"**[{t['workspace']}]** " if t.get("workspace") else ""
    if t["status"] == "done":
        done = t.get("completedAt", "") or ""
        done_date = done[:10] if done else ""
        suffix = f" _(completed {done_date})_" if done_date else ""
        return f"- [x] {ws}{t['text']}{suffix} " + " ".join(tags[1:])
    return f"- [ ] {ws}{t['text']} " + " ".join(tags)


def render_markdown(store: dict) -> str:
    todos = store.get("todos", [])
    by = {s: [t for t in todos if t.get("status") == s] for s in STATUSES}
    lines = ["# Todos", "",
             "<!-- Generated from todos.json by `cc todo`. Do not edit by hand. -->", ""]
    lines += ["## In Progress"] + ([_fmt(t) for t in _sorted(by["in_progress"])] or ["_(none)_"]) + [""]
    lines += ["## Pending"] + ([_fmt(t) for t in _sorted(by["pending"])] or ["_(none)_"]) + [""]
    done = sorted(by["done"], key=lambda t: t.get("completedAt") or "", reverse=True)
    lines += ["## Done"] + ([_fmt(t) for t in done[:20]] or ["_(none)_"]) + [""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def _find(store: dict, todo_id: int) -> dict | None:
    return next((t for t in store["todos"] if t.get("id") == todo_id), None)


def add(text: str, workspace: str = "", priority: str = "medium",
        ticket: str | None = None, source: str = "user") -> dict:
    if priority not in PRIORITIES:
        priority = "medium"
    store = load_store()
    todo = {
        "id": store["nextId"],
        "text": text,
        "workspace": workspace,
        "status": "pending",
        "priority": priority,
        "ticket": ticket,
        "source": source,
        "createdAt": _now(),
        "completedAt": None,
    }
    store["todos"].append(todo)
    store["nextId"] += 1
    save_store(store)
    return todo


def set_status(todo_id: int, status: str) -> dict | None:
    store = load_store()
    todo = _find(store, todo_id)
    if not todo:
        return None
    todo["status"] = status
    todo["completedAt"] = _now() if status == "done" else None
    save_store(store)
    return todo


def set_priority(todo_id: int, priority: str) -> dict | None:
    if priority not in PRIORITIES:
        return None
    store = load_store()
    todo = _find(store, todo_id)
    if not todo:
        return None
    todo["priority"] = priority
    save_store(store)
    return todo


def remove(todo_id: int) -> bool:
    store = load_store()
    before = len(store["todos"])
    store["todos"] = [t for t in store["todos"] if t.get("id") != todo_id]
    if len(store["todos"]) == before:
        return False
    save_store(store)
    return True


def query(status: str | None = None, workspace: str | None = None,
          ticket: str | None = None) -> list[dict]:
    todos = load_store()["todos"]
    if status:
        todos = [t for t in todos if t.get("status") == status]
    if workspace:
        todos = [t for t in todos if t.get("workspace") == workspace]
    if ticket:
        todos = [t for t in todos if t.get("ticket") == ticket]
    return _sorted(todos)


def cleanup(days: int = 30) -> int:
    store = load_store()
    cutoff = date.today().toordinal() - days
    kept, archived = [], []
    for t in store["todos"]:
        if t.get("status") == "done" and t.get("completedAt"):
            try:
                d = datetime.strptime(t["completedAt"][:10], "%Y-%m-%d").date().toordinal()
            except ValueError:
                d = cutoff + 1
            (archived if d < cutoff else kept).append(t)
        else:
            kept.append(t)
    if archived:
        with file_lock("todos-archive"):
            with ARCHIVE_MD.open("a", encoding="utf-8") as fh:
                for t in archived:
                    fh.write(_fmt(t) + "\n")
        store["todos"] = kept
        save_store(store)
    return len(archived)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _emit(obj, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2))
    elif isinstance(obj, list):
        for t in obj:
            print(_fmt(t))
    else:
        print(json.dumps(obj))


def main(argv: list[str] | None = None) -> int:
    # Shared parent so --json is accepted after any subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="JSON output")

    p = argparse.ArgumentParser(prog="cc todo", description="Command Center todo store",
                                parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="Add a todo", parents=[common])
    pa.add_argument("text")
    pa.add_argument("--workspace", default="")
    pa.add_argument("--priority", default="medium", choices=PRIORITIES)
    pa.add_argument("--ticket", default=None)
    pa.add_argument("--source", default="user", choices=("user", "lucius"))

    for name in ("done", "start", "reopen", "rm"):
        sp = sub.add_parser(name, help=f"{name} a todo by id", parents=[common])
        sp.add_argument("id", type=int)

    pp = sub.add_parser("priority", help="Change a todo's priority", parents=[common])
    pp.add_argument("id", type=int)
    pp.add_argument("level", choices=PRIORITIES)

    pl = sub.add_parser("list", help="List todos", parents=[common])
    pl.add_argument("--status", choices=STATUSES, default=None)
    pl.add_argument("--workspace", default=None)
    pl.add_argument("--ticket", default=None)

    sub.add_parser("render", help="Regenerate todos.md from todos.json", parents=[common])
    sub.add_parser("migrate", help="Import legacy todos.md into todos.json", parents=[common])
    pc = sub.add_parser("cleanup", help="Archive done items older than N days", parents=[common])
    pc.add_argument("--days", type=int, default=30)

    args = p.parse_args(argv)

    if args.cmd == "add":
        _emit(add(args.text, args.workspace, args.priority, args.ticket, args.source), args.json)
        return 0
    if args.cmd in ("done", "start", "reopen"):
        status = {"done": "done", "start": "in_progress", "reopen": "pending"}[args.cmd]
        t = set_status(args.id, status)
        if not t:
            print(f"No todo with id {args.id}", file=sys.stderr)
            return 1
        _emit(t, args.json)
        return 0
    if args.cmd == "priority":
        t = set_priority(args.id, args.level)
        if not t:
            print(f"No todo with id {args.id}", file=sys.stderr)
            return 1
        _emit(t, args.json)
        return 0
    if args.cmd == "rm":
        if not remove(args.id):
            print(f"No todo with id {args.id}", file=sys.stderr)
            return 1
        return 0
    if args.cmd == "list":
        _emit(query(args.status, args.workspace, args.ticket), args.json)
        return 0
    if args.cmd == "render":
        save_store(load_store())
        return 0
    if args.cmd == "migrate":
        store = migrate_from_markdown(TODOS_MD.read_text(encoding="utf-8")) if TODOS_MD.exists() else _empty_store()
        save_store(store)
        print(f"Migrated {len(store['todos'])} todos into {TODOS_JSON}")
        return 0
    if args.cmd == "cleanup":
        n = cleanup(args.days)
        print(f"Archived {n} done item(s).")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
