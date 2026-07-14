---
name: dashboard
description: Regenerate the static Command Center dashboard and open it in Simple Browser
---

# Dashboard command

1. Ensure tools installed: if `~/.command-center/scripts/generate-dashboard.sh` missing, run `scripts/install-mission-tools.sh` from the plugin (or `@lu init missions`).
2. Run: `"$HOME/.command-center/scripts/generate-dashboard.sh"` or plugin `scripts/generate-dashboard.sh`
3. Tell user to open Simple Browser (`Cmd+Shift+P` → **Simple Browser: Show**) with:

```
file://$HOME/.command-center/dashboard/index.html
```

Note: the page is a **snapshot** — regenerate after mission progress or todo changes.
