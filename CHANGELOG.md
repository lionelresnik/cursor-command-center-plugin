# Changelog

All notable changes to the Command Center Cursor plugin.

## [0.2.3] — 2026-07-14

### Fixed
- **`capture_pr_url`:** Append to JSON list instead of overwrite — multiple PRs in one session now preserved
- **`detect_workspace`:** Log warning to `session-debug.log` when multiple workspaces match the current directory

### Added
- `tests/test_cc_session.py` — 14 pytest cases covering session start, todo counting, ISO timestamp parsing, PR URL capture/append/dedup
- `CONTRIBUTING.md` — dev setup, plugin structure, rule loading, data paths, PR checklist

### Changed
- Easter egg (Fox Protocol) moved from `rules/easter-egg.mdc` into `agents/lucius.md` — frees a rule slot, behaviour unchanged

## [0.2.2] — 2026-07-14

### Fixed
- **install-plugin.sh:** Auto-reset dirty clones when `git pull` is blocked by local changes
- **install-plugin.sh:** `chmod +x` for `cc_session.py`, `cc_lock.py`, and all shell scripts after install

### Added
- README **Troubleshooting** section for blocked plugin updates

## [0.2.1] — 2026-07-14

### Fixed
- **Session hooks:** Replaced fragile `grep`/`sed` JSON parsing with `scripts/cc_session.py` (Python `json` + `datetime`)
- **Git leak:** `cc-context.json` and `cc-last-pr.txt` now live in `~/.command-center/` (not `.cursor/` in the project)
- **Date parsing:** ISO timestamp failures log to `~/.command-center/logs/session-debug.log` instead of silently returning idle `0`
- **Session start:** Missions/dashboard no longer auto-loaded on every session — opt-in via `@lu init missions`

### Added
- `scripts/cc_lock.py` — file locking for concurrent todo/mission writes (`~/.command-center/locks/`)
- README **Prerequisites** section (git, python3, gh)
- Manual install script seeds roles/crews/tools on install
- Demo mission seed/remove scripts (`@lu init demo missions` / `@lu remove demo missions`)
- README: Plan mode vs mission file bridge documentation

## [0.2.0] — 2026-07-14

### Added
- **Missions & crews** — multi-role workflows, behavior modes, manual handoffs, artifacts
- **Static dashboard** — `@lu dashboard` generates `~/.command-center/dashboard/index.html`
- **Workspace knowledge base** — structured docs under `docs/[workspace]/`
- **`@lu onboard`** — knowledge gap inventory
- **Daily log** integration with standups and recaps
- **Export/import v2.0** — roles, crews, missions
- **`@lu migrate from CLI`** — migration from cursor-command-center CLI
- Token efficiency guidance (`when-to-use-lu.mdc`)
- Consolidated rules and lean `@lu` usage patterns

### Merged
- PR #3 — audit & token reduction
- PR #2 — daily log tracking
- PR #1 — docs/markdown style, graph delegation, CLI migration skill

## [0.1.0] — Initial release

- Workspace management, task tracking, PR linking, git status
- Architecture graphs, todos, standups, personalization, export/import
