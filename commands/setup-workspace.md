---
name: setup-workspace
description: Create a new multi-repo workspace by scanning a directory for git repos and selecting which ones to include
---

# Setup Workspace

Guide the user through creating a new multi-repo workspace. Use the `workspace-manager` skill for full implementation details.

1. **Ask for a workspace name** — lowercase, kebab-case, no spaces
2. **Ask where repos are** — e.g., `~/Projects`
3. **Scan for repos** — show ALL found repos with numbers, never truncate
4. **Let user select** — "all", "1,3,5", "1-10, 15", "all except 2,4"
5. **Ask about additional directories** — users often have repos in multiple locations
6. **Create the workspace:**
   - Save repo list to `contexts/[name].repos`
   - Generate `~/.command-center/workspaces/[name].code-workspace` (include Command Center folder first for sidebar access)
   - Create `task-history/[name]/` and `docs/[name]/` directories
7. **Offer to open:** `cursor ~/.command-center/workspaces/[name].code-workspace`
8. **Welcome flow** — in the new workspace, offer git status, architecture graph, or starting a task
9. **Offer to generate graph** — invoke the graph-generator skill
