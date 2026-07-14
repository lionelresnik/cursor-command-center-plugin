"""Tests for cc_todos.py — JSON store, mutations, markdown migration/render."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import cc_todos  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Point all module paths at a tmp dir so tests never touch real data."""
    monkeypatch.setattr(cc_todos, "CC_DIR", tmp_path)
    monkeypatch.setattr(cc_todos, "TODOS_JSON", tmp_path / "todos.json")
    monkeypatch.setattr(cc_todos, "TODOS_MD", tmp_path / "todos.md")
    monkeypatch.setattr(cc_todos, "ARCHIVE_MD", tmp_path / "todos-archive.md")
    # cc_lock writes lock files under CC_DIR/locks via its own CC_DIR
    import cc_lock
    monkeypatch.setattr(cc_lock, "CC_DIR", tmp_path)
    monkeypatch.setattr(cc_lock, "LOCK_DIR", tmp_path / "locks")
    yield


# ---------------------------------------------------------------------------
# add / status / priority / remove
# ---------------------------------------------------------------------------

def test_add_assigns_incrementing_ids():
    a = cc_todos.add("first", workspace="platform", priority="high")
    b = cc_todos.add("second", workspace="backend")
    assert a["id"] == 1
    assert b["id"] == 2
    assert a["status"] == "pending"
    assert a["priority"] == "high"
    assert b["priority"] == "medium"  # default


def test_add_persists_json_and_md():
    cc_todos.add("persisted", workspace="platform")
    assert cc_todos.TODOS_JSON.exists()
    assert cc_todos.TODOS_MD.exists()
    data = json.loads(cc_todos.TODOS_JSON.read_text())
    assert data["todos"][0]["text"] == "persisted"
    assert "persisted" in cc_todos.TODOS_MD.read_text()


def test_done_sets_completed_at():
    t = cc_todos.add("finish me")
    done = cc_todos.set_status(t["id"], "done")
    assert done["status"] == "done"
    assert done["completedAt"] is not None


def test_start_and_reopen():
    t = cc_todos.add("cycle")
    assert cc_todos.set_status(t["id"], "in_progress")["status"] == "in_progress"
    reopened = cc_todos.set_status(t["id"], "pending")
    assert reopened["status"] == "pending"
    assert reopened["completedAt"] is None


def test_set_priority():
    t = cc_todos.add("bump", priority="low")
    assert cc_todos.set_priority(t["id"], "high")["priority"] == "high"


def test_set_priority_invalid():
    t = cc_todos.add("x")
    assert cc_todos.set_priority(t["id"], "urgent") is None


def test_remove():
    t = cc_todos.add("delete me")
    assert cc_todos.remove(t["id"]) is True
    assert cc_todos.remove(t["id"]) is False
    assert cc_todos.query() == []


def test_status_unknown_id():
    assert cc_todos.set_status(999, "done") is None


# ---------------------------------------------------------------------------
# query / ordering
# ---------------------------------------------------------------------------

def test_query_filters():
    cc_todos.add("p-high", workspace="platform", priority="high", ticket="AUTH-1")
    cc_todos.add("b-low", workspace="backend", priority="low")
    t = cc_todos.add("p-med", workspace="platform", priority="medium")
    cc_todos.set_status(t["id"], "in_progress")

    assert len(cc_todos.query(workspace="platform")) == 2
    assert len(cc_todos.query(status="in_progress")) == 1
    assert len(cc_todos.query(ticket="AUTH-1")) == 1


def test_query_priority_sorted():
    cc_todos.add("low", priority="low")
    cc_todos.add("high", priority="high")
    cc_todos.add("med", priority="medium")
    order = [t["priority"] for t in cc_todos.query()]
    assert order == ["high", "medium", "low"]


# ---------------------------------------------------------------------------
# migration from legacy markdown
# ---------------------------------------------------------------------------

LEGACY_MD = """\
# Todos

## In Progress
- [ ] **[backend]** Fix auth retry `#priority-high` `#AUTH-123` `#user`

## Pending
- [ ] **[frontend]** Mobile layout `#priority-medium` `#lucius`

## Done
- [x] **[backend]** Health check _(completed 2026-01-05)_ `#ABC-9` `#user`
"""


def test_migrate_from_markdown_parses_all_fields():
    store = cc_todos.migrate_from_markdown(LEGACY_MD)
    assert len(store["todos"]) == 3

    ip = next(t for t in store["todos"] if t["status"] == "in_progress")
    assert ip["workspace"] == "backend"
    assert ip["priority"] == "high"
    assert ip["ticket"] == "AUTH-123"
    assert ip["source"] == "user"
    assert "Fix auth retry" in ip["text"]
    assert "#" not in ip["text"]  # tags stripped

    done = next(t for t in store["todos"] if t["status"] == "done")
    assert done["completedAt"] == "2026-01-05"
    assert done["ticket"] == "ABC-9"


def test_load_store_auto_migrates(tmp_path):
    cc_todos.TODOS_MD.write_text(LEGACY_MD, encoding="utf-8")
    store = cc_todos.load_store()
    assert len(store["todos"]) == 3


# ---------------------------------------------------------------------------
# markdown render round-trip
# ---------------------------------------------------------------------------

def test_render_groups_by_status():
    cc_todos.add("pending item", workspace="platform", priority="high")
    t = cc_todos.add("active item", workspace="backend")
    cc_todos.set_status(t["id"], "in_progress")
    d = cc_todos.add("done item")
    cc_todos.set_status(d["id"], "done")

    md = cc_todos.TODOS_MD.read_text()
    assert "## In Progress" in md
    assert "## Pending" in md
    assert "## Done" in md
    assert "active item" in md
    assert "[x]" in md  # done checkbox


def test_render_empty_sections():
    cc_todos.add("only pending")
    md = cc_todos.TODOS_MD.read_text()
    assert "_(none)_" in md  # in-progress + done empty


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

def test_cleanup_archives_old_done():
    t = cc_todos.add("old task")
    cc_todos.set_status(t["id"], "done")
    # Force an old completion date
    store = cc_todos.load_store()
    store["todos"][0]["completedAt"] = "2000-01-01T00:00:00Z"
    cc_todos.save_store(store)

    archived = cc_todos.cleanup(days=30)
    assert archived == 1
    assert cc_todos.query() == []
    assert cc_todos.ARCHIVE_MD.exists()


def test_cleanup_keeps_recent_done():
    t = cc_todos.add("recent")
    cc_todos.set_status(t["id"], "done")
    assert cc_todos.cleanup(days=30) == 0
    assert len(cc_todos.query()) == 1


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def test_cli_add_and_list(capsys):
    assert cc_todos.main(["add", "via cli", "--workspace", "platform", "--json"]) == 0
    capsys.readouterr()
    assert cc_todos.main(["list", "--json"]) == 0
    out = capsys.readouterr().out
    assert "via cli" in out


def test_cli_done_unknown_returns_1():
    assert cc_todos.main(["done", "42"]) == 1
