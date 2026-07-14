# Contributing to Command Center

## Local dev setup

The fastest way is a symlink — Cursor loads the live repo directly:

```bash
rm -rf ~/.cursor/plugins/local/command-center
ln -s ~/Projects/cursor-command-center-plugin ~/.cursor/plugins/local/command-center
chmod +x ~/Projects/cursor-command-center-plugin/scripts/*.sh \
         ~/Projects/cursor-command-center-plugin/scripts/cc_session.py \
         ~/Projects/cursor-command-center-plugin/scripts/cc_lock.py
~/Projects/cursor-command-center-plugin/scripts/install-mission-tools.sh
```

Reload Cursor (`Cmd+Shift+P → Developer: Reload Window`) after any change to rules, skills, agents, or hooks. Scripts take effect immediately.

## Plugin structure

```
.cursor-plugin/plugin.json   ← manifest: name, version, declared components
agents/                      ← @lucius / @lu personality + capability list
rules/                       ← context-injected behaviour (see below)
skills/                      ← multi-step procedures invoked by Lucius
commands/                    ← /slash command definitions
hooks/hooks.json             ← shell hooks: sessionStart, sessionEnd, afterShellExecution
scripts/                     ← shell/Python scripts called by hooks
templates/                   ← default roles, crews, demo missions
assets/                      ← static files (dashboard template, easter egg art)
tests/                       ← pytest suite for scripts/cc_session.py
```

## How rules load

Rules live in `rules/*.mdc` with YAML frontmatter:

```yaml
---
description: "One sentence — used by Cursor to decide when to inject this rule."
alwaysApply: false   # true = every request; false = injected when description matches
globs: ["**/*.go"]   # optional: file-pattern scope
---
```

- `alwaysApply: true` — loaded on every `@lu` call. Use sparingly; costs tokens.
- `alwaysApply: false` — injected automatically when the prompt/context matches `description`. Prefer this.
- Keep rules focused. A 200-line rule with ten concerns is worse than three 70-line rules.

## How skills load

Skills live in `skills/<name>/SKILL.md`. Lucius reads them when the description matches the user's intent. Keep the `description:` frontmatter tight — it's the trigger.

## Testing

```bash
python3 -m pytest tests/ -v
```

Tests cover `cc_session.py` — session start, todo counting, ISO timestamp parsing, PR URL capture. Add tests there when changing session hook logic.

## Making changes

- **Rules/skills/agents:** Edit the file, reload Cursor, test with `@lu`.
- **Scripts:** Edit, `chmod +x` if new, test directly: `python3 scripts/cc_session.py start`.
- **Hooks:** Edit `hooks/hooks.json`; reload Cursor. Hook scripts receive stdin from shell output for `afterShellExecution`.
- **Data paths:** All user data is under `~/.command-center/`. The plugin dir is code-only. Never write user data into the plugin directory.

## Data locations

| Path | Contents |
|------|----------|
| `~/.command-center/cc-context.json` | Session context (workspace, idle, todos) |
| `~/.command-center/session-state.json` | Last session timestamps |
| `~/.command-center/todos.md` | Persistent todos |
| `~/.command-center/roles/`, `crews/` | Mission tooling |
| `~/.command-center/missions/` | Active/completed missions |
| `~/.command-center/logs/` | Debug logs (parse failures, skill errors) |
| `~/.command-center/locks/` | flock-based write locks |

## Versioning

Bump `version` in `.cursor-plugin/plugin.json` and add an entry to `CHANGELOG.md` for any user-visible change.

## PR checklist

- [ ] `python3 -m pytest tests/` passes
- [ ] `alwaysApply: true` rules justified (or avoided)
- [ ] No user data written to the plugin directory
- [ ] `CHANGELOG.md` updated
- [ ] Version bumped if user-facing
