---
name: migrate-from-cli
description: Migrate from cursor-command-center CLI to the plugin. Preserves all existing data (todos, task history, standups, docs, workspaces) and removes CLI-specific files. Use when the user has installed the plugin from the Cursor marketplace and wants to stop using the CLI.
---

# Migrate from CLI to Plugin

## When to Use

Use this skill when the user says things like:
- "I installed the plugin, can I remove the CLI?"
- "Migrate from CLI to plugin"
- "I want to use only the plugin now"
- "Remove CLI, keep my data"

## What Gets Preserved

All your data stays exactly where it is — the plugin reads from the same locations:

| Data | Location | Action |
|------|----------|--------|
| Todos | `~/.command-center/todos.md` | ✅ Kept as-is |
| Task history | `~/.command-center/task-history/` | ✅ Kept as-is |
| Standups | `~/.command-center/standups/` | ✅ Kept as-is |
| Docs | `~/.command-center/docs/` | ✅ Kept as-is |
| Workspaces | `~/.command-center/workspaces/` | ✅ Kept as-is |
| Profile | `~/.command-center/profile.json` | ✅ Kept as-is |
| Contexts | `~/.command-center/contexts/` | ✅ Kept as-is |

The plugin uses the same `~/.command-center/` data directory as the CLI — no migration of data needed.

## What Gets Removed

CLI-specific files that are no longer needed once the plugin is active:

- `~/.command-center/.cursor/` — rules/skills/agents copied there by the CLI's `sync.sh` (the plugin provides these natively)
- The `cursor-command-center` repo itself (optional — only if user confirms)

## Migration Steps

### Step 1: Confirm plugin is installed and active

Ask the user:
> "Before we remove the CLI, let's confirm the plugin is working. Can you open a workspace in Cursor and type `@lu what can you do?` — do you get a response?"

Only proceed after confirmation.

### Step 2: Confirm what to remove

Ask:
> "I'll remove the CLI-injected rules/skills from `~/.command-center/.cursor/` since the plugin now provides these natively. Your todos, task history, standups, docs, and workspaces are all safe — they stay in `~/.command-center/`.
>
> Do you also want to remove the `cursor-command-center` repo itself from `~/Projects/`? (You can always re-clone it later if needed)"

### Step 3: Remove CLI-injected components

After confirmation, run:

```bash
# Remove CLI-injected .cursor folder (plugin provides these natively)
rm -rf ~/.command-center/.cursor
echo "✓ Removed CLI-injected rules/skills"
```

### Step 4: Remove CLI repo (if user confirmed)

```bash
# Only if user said yes to removing the repo
rm -rf ~/Projects/cursor-command-center
echo "✓ Removed cursor-command-center repo"
```

### Step 5: Verify data is intact

```bash
echo "=== Your data is safe ==="
echo "Todos:"
cat ~/.command-center/todos.md | head -20
echo ""
echo "Task history folders:"
ls ~/.command-center/task-history/ 2>/dev/null || echo "(empty)"
echo ""
echo "Workspaces:"
ls ~/.command-center/workspaces/ 2>/dev/null || echo "(empty)"
```

### Step 6: Confirm completion

Tell the user:
> "Migration complete! The plugin is now your only source of `@lu` features. All your data (todos, task history, standups, docs, workspaces) is intact in `~/.command-center/`.
>
> The plugin reads directly from there — no sync needed. Everything works exactly as before."

## Rollback

If the user wants to go back to the CLI:

```bash
# Re-clone the CLI
git clone https://github.com/lionelresnik/cursor-command-center.git ~/Projects/cursor-command-center
cd ~/Projects/cursor-command-center
./sync.sh
```

All data is preserved since it was never deleted from `~/.command-center/`.
