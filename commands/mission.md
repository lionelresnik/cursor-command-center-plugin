---
name: mission
description: Show mission status, list crews/roles, or guide new mission / next role / complete role workflows
---

# Mission command

Use the **mission-manager** skill.

## Quick reference

| User intent | Action |
|-------------|--------|
| `/mission` or status | List active missions + next role |
| new mission | `@lu new mission "goal" crew:backend-crew` |
| start role | `@lu next role` |
| finish role | `@lu complete role` |
| setup | `@lu init missions` (repair seed — install already copies roles/crews/tools) |
| demo data | `@lu init demo missions` / `@lu remove demo missions` |

Remind user: **regular agent for coding** after `@lu next role` delivers the prompt bundle.
