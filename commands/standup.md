---
name: standup
description: Generate a daily or weekly standup summary from todos and task history
---

# Standup

Generate a standup summary. Use the `standup-generator` skill for implementation.

**Triggers:** "standup", "daily", "weekly", "what did I do", "recap my work"

1. Detect scope: **daily** (default) or **weekly** (if user says "weekly" or it's the start of the work week)
2. Generate the standup using the skill
3. Save to `~/.command-center/standups/`
4. Display inline in chat
