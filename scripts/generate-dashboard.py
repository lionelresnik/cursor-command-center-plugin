#!/usr/bin/env python3
"""Generate static Command Center dashboard from ~/.command-center data."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

CC_DIR = Path(os.environ.get("COMMAND_CENTER_DIR", Path.home() / ".command-center"))
OUT_DIR = CC_DIR / "dashboard"
OUT_FILE = OUT_DIR / "index.html"
PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def read_profile() -> dict:
    p = CC_DIR / "profile.json"
    if not p.exists():
        return {"name": ""}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {"name": ""}


def count_todos() -> dict:
    todos = CC_DIR / "todos.md"
    counts = {"pending": 0, "in_progress": 0, "done": 0}
    if not todos.exists():
        return counts
    section = ""
    for line in todos.read_text().splitlines():
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


def load_missions() -> list[dict]:
    missions_dir = CC_DIR / "missions"
    if not missions_dir.exists():
        return []
    out = []
    for d in sorted(missions_dir.iterdir()):
        if not d.is_dir():
            continue
        mf = d / "mission.json"
        if not mf.exists():
            continue
        try:
            m = json.loads(mf.read_text())
            m.setdefault("id", d.name)
            out.append(m)
        except json.JSONDecodeError:
            continue
    return out


def load_crews() -> list[dict]:
    crews_dir = CC_DIR / "crews"
    if not crews_dir.exists():
        return []
    crews = []
    for f in sorted(crews_dir.glob("*.yaml")) + sorted(crews_dir.glob("*.yml")):
        text = f.read_text()
        name = f.stem
        cid = name
        m_id = re.search(r"^id:\s*(.+)$", text, re.M)
        if m_id:
            cid = m_id.group(1).strip()
        m_name = re.search(r"^name:\s*(.+)$", text, re.M)
        display = m_name.group(1).strip() if m_name else name
        roles = re.findall(r"roleId:\s*(\S+)", text)
        chain = " → ".join(roles) if roles else "—"
        crews.append({"id": cid, "name": display, "chain": chain})
    return crews


def load_workspaces() -> list[dict]:
    ctx = CC_DIR / "contexts"
    if not ctx.exists():
        return []
    colors = ["#6366f1", "#22c55e", "#f97316", "#3b82f6", "#ec4899"]
    workspaces = []
    missions = load_missions()
    for i, repos_file in enumerate(sorted(ctx.glob("*.repos"))):
        ws = repos_file.stem
        repos = len([ln for ln in repos_file.read_text().splitlines() if "|" in ln])
        mcount = sum(1 for m in missions if m.get("workspace") == ws and m.get("status") != "done")
        workspaces.append({
            "name": ws,
            "color": colors[i % len(colors)],
            "repos": repos,
            "missions": mcount,
        })
    return workspaces


def mission_roles(m: dict) -> list[dict]:
    graph = m.get("taskGraph") or []
    summaries = m.get("artifactSummaries") or {}
    roles = []
    for node in graph:
        rid = node.get("roleId", "")
        status = node.get("status", "pending")
        if status == "running":
            status = "active"
        roles.append({
            "name": node.get("roleName") or rid,
            "status": status,
            "summary": summaries.get(rid) or ("Waiting" if status == "active" else None),
        })
    return roles


def build_data() -> dict:
    missions = load_missions()
    todos = count_todos()
    active = [m for m in missions if m.get("status") not in ("done", "failed")]
    awaiting = sum(1 for m in missions if m.get("status") == "awaiting_review")
    profile = read_profile()
    ctx_file = Path(".cursor/cc-context.json")
    workspace = ""
    if (Path.cwd() / ctx_file).exists():
        try:
            workspace = json.loads((Path.cwd() / ctx_file).read_text()).get("workspace", "")
        except json.JSONDecodeError:
            pass

    return {
        "user": {"name": profile.get("name") or "there"},
        "workspace": workspace or "—",
        "generatedAt": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z"),
        "stats": {
            "activeMissions": len(active),
            "awaitingReview": awaiting,
            "openTodos": todos["pending"] + todos["in_progress"],
            "workspaces": len(load_workspaces()),
        },
        "missions": [
            {
                "id": m.get("id"),
                "name": m.get("name", m.get("id")),
                "goal": m.get("goal", ""),
                "workspace": m.get("workspace", ""),
                "crew": m.get("crew", ""),
                "agentBehavior": m.get("agentBehavior", "assume_and_document"),
                "handoffMode": m.get("handoffMode", "manual"),
                "status": m.get("status", "pending"),
                "progress": m.get("progress", 0),
                "ticket": m.get("ticket"),
                "roles": mission_roles(m),
                "assumptions": len(m.get("artifactSummaries") or {}),
            }
            for m in sorted(missions, key=lambda x: x.get("updatedAt", ""), reverse=True)[:10]
        ],
        "workspaces": load_workspaces(),
        "crews": load_crews(),
        "todos": {"counts": todos},
    }


def render_html(data: dict) -> str:
    for candidate in (
        CC_DIR / "dashboard" / "template.html",
        PLUGIN_ROOT / "assets" / "dashboard-template.html",
    ):
        if candidate.exists():
            template = candidate.read_text()
            break
    else:
        raise SystemExit("dashboard template not found")
    payload = json.dumps(data, indent=2).replace("</", "<\\/")
    return template.replace("/*__DATA__*/", payload)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = build_data()
    OUT_FILE.write_text(render_html(data))
    print(str(OUT_FILE))


if __name__ == "__main__":
    main()
