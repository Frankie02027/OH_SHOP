# Path Classification Register

Date context: 2026-03-29

| Path | Classification | Purpose | Judgment | Why |
| --- | --- | --- | --- | --- |
| `compose/docker-compose.yml` | `ACTIVE_RUNTIME` | canonical service definition | Keep | Runtime authority. |
| `compose/openhands_override/Dockerfile` | `ACTIVE_RUNTIME` | OpenHands app build override | Keep | Canonical app image path. |
| `compose/openhands_override/apply_runtime_patches.py` | `ACTIVE_COMPATIBILITY_DEBT` | OpenHands app patch authority | Keep | Active but patch debt. |
| `compose/agent_server_override/Dockerfile` | `ACTIVE_COMPATIBILITY_DEBT` | sandbox agent-server repack | Keep | Still required to override the frozen upstream image. |
| `scripts/agent_house.py` | `ACTIVE_OPS_WRAPPER` | canonical control plane | Keep | Single operational entrypoint. |
| `scripts/up.sh` | `ACTIVE_OPS_WRAPPER` | startup wrapper | Keep | Canonical operator shortcut. |
| `scripts/down.sh` | `ACTIVE_OPS_WRAPPER` | shutdown wrapper | Keep | Canonical operator shortcut. |
| `scripts/verify.sh` | `ACTIVE_OPS_WRAPPER` | verification wrapper | Keep | Canonical verifier shortcut. |
| `scripts/verify.py` | `ACTIVE_OPS_WRAPPER` | Python verifier wrapper | Keep | Lightweight helper. |
| `scripts/backup_state.sh` | `ACTIVE_OPS_WRAPPER` | state backup helper | Keep | Legit operational tool. |
| `scripts/chat_guard.py` | `ACTIVE_COMPATIBILITY_DEBT` | manual runtime cleanup helper | Keep | Still useful, but not baseline architecture. |
| `scripts/lmstudio-docker-dnat.sh` | `ACTIVE_COMPATIBILITY_DEBT` | privileged Docker-to-host LM Studio workaround | Keep | Real manual workaround, not normal product runtime. |
| `compat/openhands_sdk_overrides/` | `ACTIVE_COMPATIBILITY_DEBT` | shared converter overlays | Keep | Active and now isolated honestly. |
| `vendor/stagehand_mcp/` | `ACTIVE_RUNTIME_SUPPORT` | extracted active browser-tool vendor slice | Keep | Current browser lane. |
| `vendor/stagehand_mcp/src/server.ts` | `ACTIVE_COMPATIBILITY_DEBT` | Stagehand MCP server with LM Studio shims | Keep | Runtime-critical compatibility shim. |
| `workspace/` | `ACTIVE_RUNTIME_SUPPORT` | only host subtree exposed to sandboxes | Keep | Clarifies workspace authority. |
| `workspace/.openhands_instructions` | `ACTIVE_COMPATIBILITY_DEBT` | hidden behavioral policy file in workspace root | Keep, flagged | Still mounted into runtime workspace; governance risk remains. |
| `data/openhands/` | `ACTIVE_RUNTIME_SUPPORT` | runtime state and persistence | Keep | Runtime-significant. |
| `downloads/` | `ACTIVE_RUNTIME_SUPPORT` | browser/download artifact target | Keep | Active compose mount. |
| `docs/current/` | `ACTIVE_EVIDENCE_DOCS` | current operator docs | Keep | Current docs surface. |
| `docs/runtime/` | `ACTIVE_EVIDENCE_DOCS` | stabilization/normalization/investigation evidence | Keep | Active pass history and runtime proof material. |
| `docs/architecture/` | `ACTIVE_ARCHITECTURE_DOCS` | target-state architecture and future design | Keep | Useful, but explicitly not runtime authority. |
| `docs/research/` | `ACTIVE_ARCHITECTURE_DOCS` | deep audits and research reports | Keep | Useful reference, not runtime authority. |
| `docs/archive/` | `HISTORICAL_ARCHIVE` | obsolete contracts and old plans | Keep | Evidence only. |
| `docs/repo_reaudit_restructure/` | `ACTIVE_EVIDENCE_DOCS` | this pass artifact set | Keep | Current repo-surface authority. |
| `artifacts/backups/` | `ACTIVE_RUNTIME_SUPPORT` | operator backups | Keep | Operational artifact storage. |
| `artifacts/benchmarks/` | `ACTIVE_RUNTIME_SUPPORT` | benchmark fixtures and runner | Keep, rehomed | Useful but not ops surface. |
| `artifacts/runtime_evidence/` | `ACTIVE_EVIDENCE_DOCS` | raw runtime logs/evidence moved out of docs surface | Keep | Evidence belongs here, not mixed into narrative docs. |
| `archive/bridge/model_router/` | `QUARANTINE` | old LM Studio hot-swap proxy | Archive | Off-path, misleading in live root. |
| `archive/bridge/openapi_server/` | `FUTURE_PLACEHOLDER` | Phase C placeholder | Archive | Explicitly non-runtime. |
| `archive/reference/OpenHands/` | `HISTORICAL_ARCHIVE` | copied upstream OpenHands tree | Archive | Reference only, misleading as runtime authority. |
| `archive/vendor_snapshots/stagehand_working/` | `HISTORICAL_ARCHIVE` | larger copied Stagehand workspace snapshot | Archive | Provenance/reference only. |
| `archive/runtime_fixtures/compose_phase1_fixture/` | `QUARANTINE` | dead Phase 1 fixture path | Archive | No longer active. |
| `archive/samples/calculator/` | `DELETE` | broken toy repo moved off active surface | Archive now, removable later | Not runtime, only evidence of junk. |
| `archive/samples/sieve.py` | `DELETE` | broken toy file moved off active surface | Archive now, removable later | Same reason. |
| `archive/samples/test_images/` | `QUARANTINE` | loose sample assets | Archive | Non-runtime clutter. |
| `.venv/` | `QUARANTINE` | local Python environment | Ignore | Developer-local only. |
| `.vscode/` | `QUARANTINE` | local editor settings | Ignore | Developer-local only. |
| `.openhands/` | `QUARANTINE` | local runtime cache/state outside repo truth | Ignore | Environment-local only. |

## Direct rulings

- `compose/` stays active because the canonical commands and runtime authority already center there.
- `scripts/` stays active because it is the actual operator surface, not cosmetic wrapper noise.
- `compat/` exists because hiding compatibility sludge under `compose/` was dishonest.
- `vendor/` exists because the active Stagehand MCP slice is real runtime support, not a user workspace repo.
- `workspace/` exists because `repos/` was an overloaded name that mixed workspace, vendor code, and junk.
- `archive/` exists because dead, placeholder, and reference code should not sit beside live runtime paths pretending to matter.
