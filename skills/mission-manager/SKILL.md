---
name: mission-manager
description: Create and run multi-role missions with crews — new mission, next role, complete role, status, checkpoint, and init defaults. File-based under ~/.command-center/missions/. Use for crew workflows; ad-hoc work stays in task-history.
---

# Mission Manager

Missions orchestrate **crews of roles** across sessions. Cursor executes each role; this skill manages files and handoffs.

**Ad-hoc work** still uses `task-history/` — missions are optional.

## Paths

| Path | Purpose |
|------|---------|
| `~/.command-center/roles/` | Role definitions (`*.md` with YAML frontmatter) |
| `~/.command-center/crews/` | Crew definitions (`*.yaml`) |
| `~/.command-center/missions/{id}/` | One folder per mission |
| `~/.command-center/missions/{id}/mission.json` | Goal, graph, status, behavior |
| `~/.command-center/missions/{id}/artifacts/` | One markdown file per completed role |
| `~/.command-center/missions/{id}/checkpoints.md` | Optional mid-role notes |

Mission `id`: `YYYY-MM-DD-slug` (e.g. `2026-07-14-fix-jwt`).

## Init defaults

**On plugin install** (and `@lu init missions`): run `scripts/install-mission-tools.sh` — copies default roles, crews, and dashboard generator into `~/.command-center/`. Idempotent; does not overwrite your custom roles/crews.

**Does not create demo missions.** For sample data: `@lu init demo missions`.

## Demo missions

**`@lu init demo missions`** (aliases: `@lu seed demo missions`)

1. Run `install-mission-tools.sh` if roles/crews are missing
2. Run `scripts/seed-demo-missions.sh` — copies 3 tagged demo missions into `~/.command-center/missions/` and writes `demo-missions.json` marker
3. Regenerate dashboard; tell user missions are prefixed `[Demo]` and safe to delete

**`@lu remove demo missions`**

1. Run `scripts/remove-demo-missions.sh` — removes missions listed in `demo-missions.json`, any `demo-*` folder, and any mission with `"demo": true` in `mission.json`
2. Keeps roles, crews, and real missions untouched
3. Regenerate dashboard

If user already has real missions, demo seed still works (skips existing folder names).

## mission.json schema

```json
{
  "id": "2026-07-14-fix-jwt",
  "name": "Fix JWT refresh loop",
  "goal": "Stop infinite 401 on token refresh",
  "workspace": "platform",
  "crew": "backend-crew",
  "ticket": "AUTH-2847",
  "agentBehavior": "assume_and_document",
  "handoffMode": "manual",
  "status": "running",
  "progress": 0,
  "taskGraph": [
    { "roleId": "backend-engineer", "roleName": "Backend Engineer", "status": "pending", "dependsOn": [] },
    { "roleId": "reviewer", "roleName": "Reviewer", "status": "pending", "dependsOn": ["backend-engineer"] }
  ],
  "artifactSummaries": {},
  "createdAt": "2026-07-14T10:00:00Z",
  "updatedAt": "2026-07-14T10:00:00Z"
}
```

**status:** `pending` | `running` | `awaiting_review` | `done` | `failed`

**agentBehavior:** `assume_and_document` | `ask_me` | `async` (same as Mission Control)

**handoffMode:** `manual` (default — pause after each role) | `auto` (offer next role immediately)

## Agent behavior instructions

Inject into every role prompt:

- **assume_and_document:** When uncertain, prefix with `ASSUMPTION:` and continue. Do not block.
- **ask_me:** If blocked, prefix up to 3 lines with `QUESTION:` and wait for user answer before continuing.
- **async:** Log open items as `ASYNC_QUESTION:` at the end and continue without blocking.

## New mission

`@lu new mission "Fix JWT refresh" crew:backend-crew workspace:platform behavior:ask_me`

1. Resolve workspace from arg or `cc-context.json`
2. Load crew YAML; build linear `taskGraph` from ordered members
3. Load role files for `roleName` from frontmatter
4. Create mission folder + `mission.json` with `status: pending`
5. Optionally link a todo or task file (`missionId` in frontmatter)
6. Set `status: running` when first role starts
7. Run `scripts/generate-dashboard.sh` if it exists (best effort)
8. Tell user: `@lu next role` to begin

## Next role

`@lu next role` or `@lu next role mission:2026-07-14-fix-jwt`

1. Find active mission (only one `running` or `awaiting_review` unless user specifies id)
2. If `status` is `awaiting_review` and `handoffMode` is `manual`, confirm user is ready to continue
3. Pick next `pending` role whose `dependsOn` roles are `done`
4. Load role markdown (body = system prompt)
5. Build **thin user prompt** (token-safe):
   - Mission name + goal + workspace
   - Current role name
   - Behavior instruction block
   - **Last completed artifact** — full text (one file max)
   - **Earlier roles** — only `artifactSummaries` lines from `mission.json`
   - **Doc index** — read `docs/[workspace]/_index.md` if exists; else list doc filenames + first heading only (no full doc bodies)
   - Optional: link to active task-history file if `ticket` or `taskFile` set
6. Mark role `running` in graph; update `mission.json`
7. Present prompts clearly; tell user to **switch to regular agent for coding** if the work is implementation-heavy

## Complete role

`@lu complete role` — user provides artifact content (from chat) or you summarize the session output.

1. Save `artifacts/{roleId}.md` with frontmatter (role, completedAt)
2. Add 1–2 line summary to `artifactSummaries[roleId]`
3. Mark role `done` in graph; recalc `progress` (done/total × 100)
4. Extract `ASSUMPTION:` lines → append to `docs/[workspace]/assumptions.md` (or per assumption-capture rule)
5. If more roles pending:
   - `handoffMode: manual` → set `status: awaiting_review`, show review block
   - `handoffMode: auto` → set `status: running`, show next role name
6. If all roles done → `status: done`
7. Regenerate dashboard (best effort)

### Handoff review block (manual mode)

```
✓ {roleName} complete — artifact saved
Summary: {artifactSummaries[roleId]}
Progress: {n}/{total} roles
Assumptions logged: {count}

Mission paused for review.
  @lu next role       — continue
  @lu mission status  — full graph
  @lu dashboard       — open visual board
```

## Mission status

`@lu mission status` — list active and recent missions with graph, status, next role. No full artifact dumps unless user asks.

## Checkpoint

`@lu checkpoint "Still investigating middleware order"` — append timestamped line to `checkpoints.md` for the running mission.

## List / setup

- `@lu list roles` — scan `roles/*.md`
- `@lu list crews` — scan `crews/*.yaml`
- `@lu add role "Security Reviewer"` — create role file from template
- `@lu add crew "security-crew"` — create crew YAML (user defines members)

## Dashboard

`@lu dashboard` — run `~/.command-center`-relative or plugin `scripts/generate-dashboard.sh` to write `~/.command-center/dashboard/index.html`, then tell user to open Simple Browser:

```
file://$HOME/.command-center/dashboard/index.html
```

Regenerate after: complete role, new mission, session start (hook).

## Task file link

When creating a mission from an active task, add to task frontmatter:

```yaml
missionId: 2026-07-14-fix-jwt
```

When creating standalone mission with ticket, reuse existing task file if found.

## Token rules

- Never load all `docs/` bodies into the role prompt
- Never replay all artifacts in full — summaries + last artifact only
- Mission status in chat should be short; use dashboard for visual overview
