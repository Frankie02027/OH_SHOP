# Bridge Disposition

Date context: 2026-03-29

## Final ruling

Nothing under the old `bridge/` subtree is active runtime.

It was left at the root too long and made the repo look like it had a second integration/control plane when it did not.

## Path-by-path

| Path | What it is | Status before | Final disposition | Why |
| --- | --- | --- | --- | --- |
| `archive/bridge/model_router/router.ts` | Bun LM Studio hot-swap/router proxy | off-path compatibility prototype | Archived | Not used by compose, not used by `agent_house.py`, not part of current provider path |
| `archive/bridge/model_router/start.sh` | launcher for the above proxy | off-path helper | Archived | Hardcoded local path, not canonical ops |
| `archive/bridge/model_router/package.json` | package manifest for the above proxy | off-path support file | Archived | Same reason |
| `archive/bridge/openapi_server/README.md` | explicit Phase C placeholder | future-only placeholder | Archived | It says placeholder itself; it should never have been in the live root |

## Why archive instead of delete

- `model_router` is real code, even if dead in the current runtime.
- `openapi_server` is useful only as evidence of an abandoned or deferred bridge idea.
- Both are better kept in `archive/bridge/` than left in a top-level `bridge/` directory that lies about current repo shape.
