---
name: onboard
description: Workspace knowledge base gap finder. Shows what infrastructure knowledge is already documented and what's missing for a workspace — databases, cloud resources, logs, services. Invoke with "@lu onboard [workspace]" or "@lu onboard" for current workspace.
---

# Onboard Skill

## Purpose

This skill does **not** run an upfront interview. It shows you what's already known and what's missing — then you decide whether to fill gaps now or leave them for when you encounter them naturally.

Knowledge fills in two ways:
1. **Passively** — `infrastructure-knowledge.mdc` captures things as you work
2. **Explicitly** — you tell `@lu` something and it writes it down

This skill is the **inventory view** and optional **gap filler**.

---

## Steps

### Step 1: Resolve Workspace

Read `~/.command-center/cc-context.json` for the `"workspace"` field.
If not found, use the workspace name provided by the user (e.g., `@lu onboard backend` → workspace is `backend`).

### Step 2: Read Existing Docs

Check `~/.command-center/docs/[workspace]/` for these files:
- `databases.md`
- `infrastructure.md`
- `logs.md`
- `services.md`
- `runbooks/` directory

For each file that exists, read it and extract a one-line summary of what's documented.

### Step 3: Present the Gap Report

Format output like this:

```
Knowledge base for [workspace]:

✅ Databases      — 3 services documented (Postgres, Redis, DynamoDB)
✅ Logs           — CloudWatch paths for api-service and worker
❓ Infrastructure — not documented yet
❓ Services       — not documented yet
❓ Runbooks       — none yet

Gaps: infrastructure, services, runbooks
```

Use:
- `✅` if the doc exists and has content beyond just the template headers
- `⚠️` if the doc exists but looks mostly empty or template-only
- `❓` if the doc doesn't exist at all

### Step 4: Offer to Fill Gaps (optional)

After the report, ask once:

> "Want to fill in any gaps now? Just tell me what you know — or say 'skip' to leave it for when we encounter it."

If the user wants to fill gaps:
- Ask one topic at a time, starting with the biggest gap
- For each answer, write it to the correct doc immediately
- Confirm each write in one line
- Stop when the user says "done", "skip", "later", or stops responding

If the user says skip/later/no — confirm:
> "Got it. I'll capture things as we discover them."

### Step 5: Explicit Notes Mode

If the user uses this skill to record something specific (e.g., `@lu onboard — the prod DB is at db.prod.internal`):
- Write it immediately to the correct doc
- Don't run the full gap report
- Confirm in one line and move on

---

## Questions to Ask Per Topic (if filling gaps)

Only ask these if the user wants to fill gaps actively. Ask them conversationally, not as a form.

### Databases
- What databases does this workspace use? (Postgres, MySQL, Redis, DynamoDB, etc.)
- Which service uses which database?
- How do you connect locally? Any port-forwarding or local replica setup?
- Is there anything special about prod access (read replicas, bastion host, etc.)?

### Infrastructure (Cloud)
- Which cloud provider(s)? (AWS/GCP/Azure)
- Any account IDs or project names worth noting?
- What cloud resources does this workspace use? (S3 buckets, SQS queues, Lambda functions, etc.)
- Anything in multiple regions?

### Logs
- Where do logs go? (CloudWatch, Datadog, Grafana, Splunk, local files, etc.)
- How do you tail or search logs for a specific service?
- Any log groups or namespaces worth noting by name?

### Services
- What services make up this workspace?
- Which repos are involved?
- Any external dependencies (Stripe, SendGrid, third-party APIs)?
- Are there any service-to-service dependencies worth mapping?

### Runbooks
- Any common operational tasks that are worth documenting? (deploy, rollback, rotate secrets, connect to prod DB)
- Any incident response steps that always get forgotten?

---

## Writing Rules

- Write to `~/.command-center/docs/[workspace]/[doc-type].md`
- If the file doesn't exist, create it using the template from `infrastructure-knowledge.mdc`
- Add to existing sections — don't overwrite the whole file
- Mark anything unverified as `> ⚠️ **Assumed** — not verified in source code`
- After writing, tell the user exactly what was written and where (one line)
