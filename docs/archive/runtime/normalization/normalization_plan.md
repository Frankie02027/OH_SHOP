# Normalization Plan

Date context: 2026-03-29

This artifact records what was changed in the runtime normalization pass and what was deliberately deferred.

## Cleanup actions taken

### Build authority

1. Pinned the OpenHands app base image in `compose/openhands_override/Dockerfile`.
2. Pinned the sandbox agent-server base image in `compose/agent_server_override/Dockerfile`.
3. Pinned OpenWebUI in `compose/docker-compose.yml`.
4. Gave Stagehand an honest local image tag in `compose/docker-compose.yml`.
5. Regenerated the `packages/mcp/package-lock.json` for the standalone Stagehand MCP slice.
6. Kept Stagehand on `npm ci` after the lockfile was repaired.
7. Updated `repos/stagehand(working)/.gitignore` so `packages/mcp/package-lock.json` is no longer silently ignored.

### Patch authority

1. Moved the winning OpenHands app patch helper into:
- `compose/openhands_override/apply_runtime_patches.py`

2. Collapsed shared converter overrides into:
- `compose/shared_vendor_sdk/`

3. Rewired both OpenHands Dockerfiles to consume that shared converter authority.

4. Removed non-winning patch debris:
- `scripts/patch_openhands_tool_call_mode.py`
- `compose/agent_server_override/vendor_sdk/*`
- `compose/agent_server_override/vendor_sdk/vendor_sdk/*`
- `repos/stagehand(working)/packages/mcp/src/server.ts.bak`

### Startup/control/config authority

1. Changed `scripts/agent_house.py` to build the sandbox image from repo root with an explicit Dockerfile path.
2. Added `OH_SHOP_ROOT` as the bind-mount path authority for canonical compose runs.
3. Removed the stale partial compose file:
- `compose/openhands.compose.yml`

### Live operational docs

1. Updated `docs/SETUP.md` to stop listing the deleted compose subset as if it still exists.
2. Updated `docs/TROUBLESHOOTING.md` to point operators back to `scripts/up.sh` and `compose/docker-compose.yml`.
3. Updated `scripts/backup_state.sh` to stop backing up the deleted compose subset.

## Cleanup actions deferred

1. Full lockfile-level Python dependency reproducibility for the sandbox image.
- Top-level sandbox package versions are explicit.
- Full pip transitive locking is still deferred.

2. Cleanup of stale local Stagehand `.env` files.
- They do not win at runtime.
- They are still misleading local residue.

3. Cleanup of tracked OpenHands runtime state under `data/openhands/`.
- This pass did not redesign state storage.
- Proof runs still mutate `openhands.db` and mirrored conversation files.

4. Cleanup of stale cached local Docker tags such as:
- `oh-stagehand-mcp:latest`
- `oh-shop/openhands:61470a1-python-patched`
- `oh-shop/agent-server:61470a1-python-patched`

Those cached tags are no longer runtime authority, but they still exist locally.

5. Broader repo quarantine cleanup outside the runtime lane.
- `bridge/model_router/`
- `bridge/openapi_server/`
- `repos/OpenHands/`

Those were not deleted in this pass because the goal was runtime normalization, not broad tree removal.

## Why the pass stopped here

The normalized runtime path itself rebuilt successfully.
The blocking issue during reverify/proof was not repo wiring.
It was host provider unavailability:
- LM Studio was down on `http://localhost:1234`
- `lms` could not connect to or start a daemon
- launching the installed LM Studio AppImage from this shell did not restore the local server

That means the remaining failure boundary at the end of this pass is host-environment state, not unresolved runtime-normalization ambiguity inside the repo.
