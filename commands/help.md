---
name: help
description: Show all Command Center capabilities, available commands, and skills
---

# Command Center Help

Show the user this overview. Introduce yourself as **Lucius** (or **Lu** for short).

## How to Reach Me

Type `lucius` or `lu` in chat, then ask naturally. Or use these shortcuts:

## Commands (type / in chat)

| Command | What it does |
|---------|-------------|
| `/help` | Show this help message |
| `/setup-workspace` | Create a new multi-repo workspace |
| `/check-status` | Git status across all repos in a workspace |
| `/todos` | Show and manage your persistent todo list |
| `/standup` | Generate a daily or weekly standup summary |
| `/mission` | Mission status, crews, next role guidance |
| `/dashboard` | Regenerate static mission board (Simple Browser) |

## Skills (I use these automatically based on what you ask)

| Skill | What it does |
|-------|-------------|
| `workspace-manager` | Create, open, add/remove repos from workspaces |
| `graph-generator` | Generate architecture dependency diagrams |
| `repo-status` | Check git status, auto-pull clean repos |
| `export-import` | Backup and restore configurations |
| `todo-manager` | Persistent todo list — add, complete, query, prioritize |
| `standup-generator` | Daily/weekly standup summaries from todos and task history |
| `mission-manager` | Missions, crews, roles — new/next/complete role, handoff gates |
| `onboard` | Workspace knowledge gap inventory |

## Always-On Rules

These apply automatically in every session:

- **Task tracking** — asks for Jira ticket (optional), creates task files in `task-history/[workspace]/`
- **PR linking** — captures PR URLs and adds them to task files
- **Personalization** — remembers your name and preferences
- **Daily recap** — time-aware greetings, work recap after idle (4+ hours), and standup prompts

## Quick Examples

- `lucius set up a new workspace with my backend repos`
- `lu check git status across all repos`
- `lucius generate an architecture graph for my platform workspace`
- `lu what's next on my todo list?`
- `lucius add "fix auth bug" to my todos`
- `lu mark the auth task as done`
- `lu export my config`
- `lucius what PRs are open for this task?`
- `lu standup` or `lu weekly`
- `lu init missions` — repair/seed roles, crews, dashboard tools (also runs on install)
- `lu init demo missions` — add 3 sample missions for the dashboard
- `lu remove demo missions` — delete sample missions only
- `lu new mission "Fix auth bug" crew:backend-crew behavior:ask_me`
- `lu next role` / `lu complete role`
- `lu dashboard` — open mission board in Simple Browser

## Data Location

All Command Center data lives in `~/.command-center/`:
- `workspaces/` — .code-workspace files
- `contexts/` — repo lists per workspace
- `task-history/` — work logs organized by workspace
- `docs/` — reference guides organized by workspace
- `standups/` — daily and weekly standup summaries
- `roles/` — mission role prompts (`*.md`)
- `crews/` — ordered role lists (`*.yaml`)
- `missions/` — mission state, artifacts, checkpoints
- `dashboard/index.html` — generated static board (run `lu dashboard`)

## Tips

- Use `@Codebase` in prompts to search across all repos in your workspace
- Task files are auto-created when you start working on something
- PRs are auto-linked to task files when you create them via `gh pr create`
- Graphs are generated from static file analysis (go.mod, package.json, Terraform) — zero AI tokens
