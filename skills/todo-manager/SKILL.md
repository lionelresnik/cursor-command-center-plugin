---
name: todo-manager
description: Manage a persistent todo list across workspaces and sessions. Add, complete, prioritize, and query todos via the `cc todo` CLI. Use when the user asks about tasks, what's next, what's done, or wants to track work items.
---

# Todo Manager

## Storage — use the `cc todo` CLI, never hand-edit files

Source of truth is **`~/.command-center/todos.json`**. A human-readable **`~/.command-center/todos.md`** is regenerated automatically on every mutation. **Do not edit either file directly** — call the CLI. It handles IDs, ordering, locking, dates, and the markdown view for you.

The CLI lives in the plugin's `scripts/` directory. Invoke it via python3:

```bash
python3 "$CC_PLUGIN/scripts/cc" todo <command>
# $CC_PLUGIN = ~/.cursor/plugins/local/command-center
```

### Commands

| Intent | Command |
|--------|---------|
| Add | `cc todo add "Fix auth" --workspace platform --priority high --ticket AUTH-123 --source user` |
| Lucius-detected add | `cc todo add "Repo behind main" --workspace platform --source lucius` |
| Mark done | `cc todo done <id>` |
| Start (→ in progress) | `cc todo start <id>` |
| Reopen (→ pending) | `cc todo reopen <id>` |
| Remove | `cc todo rm <id>` |
| Change priority | `cc todo priority <id> high` |
| List all | `cc todo list --json` |
| Filter | `cc todo list --status pending --workspace platform --ticket AUTH-123 --json` |
| Archive old done | `cc todo cleanup --days 30` |

**Always pass `--json`** when you need to read results — parse the JSON, then present it to the user in the display format below. Never parse `todos.md`.

`add` prints the created todo (including its `id`) as JSON. Use that `id` for follow-up `done`/`start`/`rm`.

Priorities: `high` \| `medium` \| `low` (default `medium`). Statuses: `pending` \| `in_progress` \| `done`.

Concurrency and the markdown view are handled by the CLI (atomic write + `~/.command-center/locks/`). You never manage locks yourself for todos.

### Ticket/Task Tagging

Todos can be optionally tagged with a ticket ID (e.g., `#PROJ-123`, `#ABC-1234`) to link them to specific tasks or Jira tickets. This allows filtering todos by ticket.

Format: `#TICKET-ID` (uppercase, placed before source tag)

## Todo Sources

Every todo is tagged with its origin:

- **`#user`** — The user explicitly asked to add it ("add this to my list", "remind me to", "don't forget")
- **`#lucius`** — Lucius detected it and suggested it (e.g., noticed a failing test, spotted a TODO comment, saw a PR needs follow-up, detected a repo is behind main)

When showing todos, always indicate the source so the user knows what they asked for vs what Lucius noticed.

## Auto-Completion

Lucius must actively track and auto-complete `#lucius` todos when the underlying issue is resolved:
- PR was merged → mark the related todo done
- Test was fixed → mark the related todo done
- Repo was pulled/synced → mark "repo behind" todo done
- Task file was completed → mark related todo done

For `#user` todos, always **ask** before marking done: "Looks like [task] might be done — should I mark it complete?"

## Operations

### Add a todo
When the user says "add todo", "remind me to", "I need to", "don't forget":
1. Detect the workspace (in order): `~/.command-center/cc-context.json` `"workspace"` field → open `.code-workspace` filename → ask. **Never default to "shared"** unless the todo explicitly spans workspaces.
2. Detect ticket ID from context (task file being worked on, task frontmatter `ticket:`, or the user's message). Skip if none.
3. Ask priority if not obvious (default medium).
4. Run: `cc todo add "<text>" --workspace <ws> --priority <p> [--ticket <T>] --source user`
5. Confirm from the returned JSON: "Added (#<id>): [task] ([workspace], [priority][, ticket])."

### Lucius-initiated todo
When Lucius detects something that needs attention:
1. Run: `cc todo add "<text>" --workspace <ws> --priority <p> --source lucius`
2. Tell the user: "I added a todo (#<id>): [task] — I noticed [reason]."

### Complete a todo
When the user says "done with", "finished", "completed", "mark as done":
1. Resolve the todo id (`cc todo list --json`, match by text/ticket).
2. Run: `cc todo done <id>`
3. Confirm: "Marked done (#<id>): [task]."

### Start working on a todo
When the user says "working on", "starting", "picking up":
1. Resolve the id, then run: `cc todo start <id>`
2. Confirm: "In progress (#<id>): [task]."

### Query todos
Always query via `cc todo list ... --json`, then present. Never read `todos.md`.

- **"What's next?"** → `cc todo list --status pending --json` → show top (list is priority-sorted)
- **"What am I working on?"** → `cc todo list --status in_progress --json`
- **"What's done?"** → `cc todo list --status done --json` → show recent
- **"What's left?"** → `cc todo list --json` → Pending + In Progress counts and list
- **"Have I forgotten something?"** → `cc todo list --status pending --json` → highlight items with old `createdAt`
- **"Show all todos"** → `cc todo list --json` grouped by status
- **"Show todos for [workspace]"** → `cc todo list --workspace <ws> --json`
- **"What's left for [TICKET-ID]?"** → `cc todo list --ticket <T> --json`
- **"What tickets do I have todos for?"** → `cc todo list --json`, collect unique `ticket` values

### Display format (chat)

When displaying todos in chat, use this Confluence-like format. This is **presentation only** — the storage (`todos.json`) and the generated `todos.md` are managed by the CLI:

```markdown
## Your Todos

### 🔄 In Progress
- **[workspace]** Task description `⚡ high` `#TICKET-123` `#user`

### 📌 Pending
- **[workspace]** Task description `⚡ high` `#ABC-456` `#user`
- **[workspace]** Task description `#lucius`

### ✅ Recently Done
- ~~Task description~~ _(completed Feb 26)_ `#TICKET-123` `#user`
```

When filtering by ticket (e.g., "what's left for PROJ-123?"), show:
```markdown
## Todos for PROJ-123

### 🔄 In Progress (2)
- **[backend]** Fix auth retry logic `⚡ high` `#user`
- **[backend]** Update API docs `#lucius`

### 📌 Pending (1)
- **[backend]** Test in staging environment `⚡ medium` `#user`

### ✅ Done (3)
- ~~Investigate root cause~~ _(completed Feb 22)_ `#user`
```

### Prioritize
- **"This is urgent"** → `cc todo priority <id> high`
- **"Reprioritize"** → `cc todo list --json`, show pending, then `cc todo priority <id> <level>` per change.

### Clean up
- **"Clean up done items"** → `cc todo cleanup --days 30` (archives to `~/.command-center/todos-archive.md`)

## Cross-Workspace View

Todos span all workspaces. Each todo is tagged with its workspace name in bold brackets. When showing todos, group by workspace if the user asks, or show flat list sorted by priority by default.

## Integration with Task Tracking

When a task file is created in `task-history/`, suggest adding a corresponding todo if one doesn't exist. Automatically tag the todo with the ticket ID from the task file's frontmatter.

When a todo is completed, check if there's a related task file to update. If the task file's status is `in-progress` and all todos for that ticket are done, suggest updating the task file status to `complete`.

When filtering todos by ticket (e.g., "what's left for PROJ-123?"), also show a link to the task file if it exists:
```
📄 Task file: task-history/backend/PROJ-123-auth-retry-fix.md
```

## Proactive Behavior

- At session start (after greeting), if there are in-progress items, mention them briefly
- If a todo has been pending for more than 7 days, gently remind the user
- When the user finishes a PR or task, ask if the related todo should be marked done
