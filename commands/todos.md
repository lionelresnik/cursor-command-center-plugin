---
name: todos
description: Show, add, or manage your persistent todo list across all workspaces
---

# Todos

Read `~/.command-center/todos.md` and present the user's todo list.

If the file doesn't exist, say: "No todos yet. Tell me what you're working on and I'll start tracking it."

If it exists, show a summary:

1. **In Progress** items first (what you're currently working on)
2. **Pending** items grouped by priority (high → medium → low)
3. **Recently Done** (last 5 completed items)

Then ask: "Want to add something, mark something done, or ask what's next?"
