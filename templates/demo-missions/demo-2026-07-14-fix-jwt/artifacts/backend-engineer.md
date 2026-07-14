---
role: backend-engineer
roleName: Backend Engineer
completedAt: "2026-07-14T11:30:00Z"
demo: true
---

## Summary

Excluded `/auth/refresh` from the global JWT middleware so refresh tokens are not validated with the same rules as access tokens.

## Changes

- `auth/middleware.go` — skip list for refresh path
- `auth/middleware_test.go` — regression test for 401 loop

## Test plan

- `go test ./auth/...`
- Manual: expire access token, confirm refresh succeeds once

## Follow-ups

- Reviewer should confirm no other public routes were accidentally skipped
