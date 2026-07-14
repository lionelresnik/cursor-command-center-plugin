"""Minimal tests for cc_session.py — session start, todo counting, ISO parsing."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Allow importing cc_session without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import cc_session  # noqa: E402


# ---------------------------------------------------------------------------
# parse_iso_timestamp
# ---------------------------------------------------------------------------

class TestParseIsoTimestamp:
    def test_z_suffix(self):
        dt = cc_session.parse_iso_timestamp("2026-07-14T10:00:00Z")
        assert dt is not None
        assert dt.tzinfo is not None
        assert dt.year == 2026

    def test_offset_aware(self):
        dt = cc_session.parse_iso_timestamp("2026-07-14T13:00:00+03:00")
        assert dt is not None
        # Should be normalised to UTC = 10:00
        assert dt.hour == 10

    def test_empty_string(self):
        assert cc_session.parse_iso_timestamp("") is None

    def test_none_like_empty(self):
        assert cc_session.parse_iso_timestamp("   ") is None

    def test_garbage(self):
        assert cc_session.parse_iso_timestamp("not-a-date") is None

    def test_naive_datetime_treated_as_utc(self):
        # fromisoformat accepts naive; we tag it UTC
        dt = cc_session.parse_iso_timestamp("2026-07-14T10:00:00")
        assert dt is not None
        assert dt.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# count_todos
# ---------------------------------------------------------------------------

TODOS_FIXTURE = """\
# Todos

## In Progress
- [ ] **[backend]** Fix auth bug `#priority-high` `#user`
- [ ] **[platform]** Review PR `#priority-med` `#lucius`

## Pending
- [ ] **[backend]** Write tests `#priority-low` `#user`

## Done
- [x] **[backend]** Deploy staging _(completed 2026-07-13)_ `#user`
- [x] **[backend]** Hotfix login _(completed 2026-07-12)_ `#lucius`
"""


def test_count_todos(tmp_path, monkeypatch):
    todos_file = tmp_path / "todos.md"
    todos_file.write_text(TODOS_FIXTURE, encoding="utf-8")
    monkeypatch.setattr(cc_session, "TODOS_FILE", todos_file)

    counts = cc_session.count_todos()
    assert counts["in_progress"] == 2
    assert counts["pending"] == 1
    assert counts["done"] == 2


def test_count_todos_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cc_session, "TODOS_FILE", tmp_path / "nonexistent.md")
    counts = cc_session.count_todos()
    assert counts == {"pending": 0, "in_progress": 0, "done": 0}


# ---------------------------------------------------------------------------
# session_start
# ---------------------------------------------------------------------------

def test_session_start_writes_context(tmp_path, monkeypatch):
    monkeypatch.setattr(cc_session, "CC_DIR", tmp_path)
    monkeypatch.setattr(cc_session, "CONTEXT_FILE", tmp_path / "cc-context.json")
    monkeypatch.setattr(cc_session, "STATE_FILE", tmp_path / "session-state.json")
    monkeypatch.setattr(cc_session, "PROFILE_FILE", tmp_path / "profile.json")
    monkeypatch.setattr(cc_session, "TODOS_FILE", tmp_path / "todos.md")

    (tmp_path / "profile.json").write_text(
        json.dumps({"name": "Lionel", "workWeek": "mon-fri"}), encoding="utf-8"
    )

    cc_session.session_start(tmp_path)

    ctx_file = tmp_path / "cc-context.json"
    assert ctx_file.exists(), "cc-context.json not written"
    ctx = json.loads(ctx_file.read_text())

    assert ctx["userName"] == "Lionel"
    assert ctx["workWeek"] == "mon-fri"
    assert "timeOfDay" in ctx
    assert "idleHours" in ctx
    assert ctx["todosPending"] == 0


def test_session_start_first_run_no_state(tmp_path, monkeypatch):
    """No state file → idle_hours should be 0, not crash."""
    monkeypatch.setattr(cc_session, "CC_DIR", tmp_path)
    monkeypatch.setattr(cc_session, "CONTEXT_FILE", tmp_path / "cc-context.json")
    monkeypatch.setattr(cc_session, "STATE_FILE", tmp_path / "session-state.json")
    monkeypatch.setattr(cc_session, "PROFILE_FILE", tmp_path / "profile.json")
    monkeypatch.setattr(cc_session, "TODOS_FILE", tmp_path / "todos.md")

    cc_session.session_start(tmp_path)

    ctx = json.loads((tmp_path / "cc-context.json").read_text())
    assert ctx["idleHours"] == 0
    assert ctx["userName"] == ""


# ---------------------------------------------------------------------------
# capture_pr_url
# ---------------------------------------------------------------------------

def test_capture_pr_url_single(tmp_path, monkeypatch):
    monkeypatch.setattr(cc_session, "CC_DIR", tmp_path)
    monkeypatch.setattr(cc_session, "PR_DETECT_FILE", tmp_path / "cc-last-pr.txt")

    cc_session.capture_pr_url("https://github.com/org/repo/pull/42\n")

    stored = json.loads((tmp_path / "cc-last-pr.txt").read_text())
    assert stored == ["https://github.com/org/repo/pull/42"]


def test_capture_pr_url_appends(tmp_path, monkeypatch):
    monkeypatch.setattr(cc_session, "CC_DIR", tmp_path)
    pr_file = tmp_path / "cc-last-pr.txt"
    monkeypatch.setattr(cc_session, "PR_DETECT_FILE", pr_file)

    cc_session.capture_pr_url("https://github.com/org/repo/pull/1\n")
    cc_session.capture_pr_url("https://github.com/org/repo/pull/2\n")

    stored = json.loads(pr_file.read_text())
    assert stored == [
        "https://github.com/org/repo/pull/1",
        "https://github.com/org/repo/pull/2",
    ]


def test_capture_pr_url_deduplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(cc_session, "CC_DIR", tmp_path)
    pr_file = tmp_path / "cc-last-pr.txt"
    monkeypatch.setattr(cc_session, "PR_DETECT_FILE", pr_file)

    cc_session.capture_pr_url("https://github.com/org/repo/pull/1\n")
    cc_session.capture_pr_url("https://github.com/org/repo/pull/1\n")

    stored = json.loads(pr_file.read_text())
    assert stored == ["https://github.com/org/repo/pull/1"]


def test_capture_pr_url_no_match(tmp_path, monkeypatch):
    monkeypatch.setattr(cc_session, "CC_DIR", tmp_path)
    monkeypatch.setattr(cc_session, "PR_DETECT_FILE", tmp_path / "cc-last-pr.txt")

    cc_session.capture_pr_url("nothing interesting here")

    assert not (tmp_path / "cc-last-pr.txt").exists()
