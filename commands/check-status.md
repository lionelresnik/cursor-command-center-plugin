---
name: check-status
description: Quick git status check across all repos in the current or specified workspace
---

# Check Status

Run a git status check across all repos:

1. **Detect workspace** from `.cursor/cc-context.json` or ask the user
2. **Read repo list** from `contexts/[workspace].repos`
3. **For each repo**, run git fetch and check status
4. **Display summary** grouped by workspace
5. **If repos are behind**, ask: "Some repos are behind. Pull the clean ones?"
6. **If yes**, auto-pull repos with clean working trees

Use the `repo-status` skill for the implementation details.
