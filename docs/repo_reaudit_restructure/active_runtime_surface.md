# Active Runtime Surface

Date context: 2026-03-29

## Active runtime files

- `compose/docker-compose.yml`
- `compose/openhands_override/Dockerfile`
- `compose/openhands_override/apply_runtime_patches.py`
- `compose/agent_server_override/Dockerfile`
- `compat/openhands_sdk_overrides/fn_call_converter.py`
- `compat/openhands_sdk_overrides/fn_call_converter_v0.py`
- `vendor/stagehand_mcp/Dockerfile`
- `vendor/stagehand_mcp/package.json`
- `vendor/stagehand_mcp/package-lock.json`
- `vendor/stagehand_mcp/tsconfig.json`
- `vendor/stagehand_mcp/src/server.ts`
- `vendor/stagehand_mcp/src/smoke.ts`
- `data/openhands/settings.json`

## Active ops wrappers

- `scripts/agent_house.py`
- `scripts/up.sh`
- `scripts/down.sh`
- `scripts/verify.sh`
- `scripts/verify.py`
- `scripts/backup_state.sh`

## Active runtime support

- `workspace/`
- `downloads/`
- `data/openhands/`
- `artifacts/backups/`

## Active compatibility debt

- `compose/openhands_override/apply_runtime_patches.py`
- `compose/agent_server_override/Dockerfile`
- `compat/openhands_sdk_overrides/*`
- `vendor/stagehand_mcp/src/server.ts`
- `scripts/chat_guard.py`
- `scripts/lmstudio-docker-dnat.sh`
- `workspace/.openhands_instructions`

## Active docs

- current operator docs:
  - `docs/current/SETUP.md`
  - `docs/current/TROUBLESHOOTING.md`
  - `docs/current/SECURITY.md`
- runtime evidence docs:
  - `docs/runtime/`
- repo-surface authority for this pass:
  - `docs/repo_reaudit_restructure/`

## Non-runtime but intentionally retained

- `docs/architecture/`
- `docs/research/`
- `docs/archive/`
- `archive/`
- `artifacts/benchmarks/`
- `artifacts/capability_tests/`
