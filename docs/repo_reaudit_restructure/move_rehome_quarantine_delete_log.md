# Move / Rehome / Quarantine / Delete Log

Date context: 2026-03-29

## Moved or rehomed

- `compose/shared_vendor_sdk/`
  -> `compat/openhands_sdk_overrides/`
  Reason: active compatibility overlays should not hide inside normal runtime folders.

- extracted active Stagehand MCP slice:
  - `repos/stagehand(working)/Dockerfile.mcp`
  - `repos/stagehand(working)/packages/mcp/package.json`
  - `repos/stagehand(working)/packages/mcp/package-lock.json`
  - `repos/stagehand(working)/packages/mcp/tsconfig.json`
  - `repos/stagehand(working)/packages/mcp/.env.example`
  - `repos/stagehand(working)/packages/mcp/src/*`
  -> `vendor/stagehand_mcp/`
  Reason: active browser-lane support now lives in an honest vendor runtime path.

- `repos/stagehand(working)/`
  -> `archive/vendor_snapshots/stagehand_working/`
  Reason: larger copied upstream workspace retained only for provenance/reference.

- `repos/OpenHands/`
  -> `archive/reference/OpenHands/`
  Reason: copied upstream reference tree is not runtime authority.

- `repos/.openhands_instructions`
  -> `workspace/.openhands_instructions`
  Reason: if it influences OpenHands at all, it belongs in the workspace root, not beside vendored code.

- `repos/calculator/`
  -> `archive/samples/calculator/`
  Reason: toy junk removed from live-looking workspace surface.

- `repos/sieve.py`
  -> `archive/samples/sieve.py`
  Reason: same.

- `repos/test_images/`
  -> `archive/samples/test_images/`
  Reason: same.

- `bridge/model_router/`
  -> `archive/bridge/model_router/`
  Reason: off-path compatibility prototype, not live runtime.

- `bridge/openapi_server/`
  -> `archive/bridge/openapi_server/`
  Reason: explicit placeholder, not live runtime.

- `scripts/benchmark_runner.py`
  -> `artifacts/benchmarks/benchmark_runner.py`
  Reason: benchmark harness is not an ops wrapper.

- raw investigation evidence:
  - `docs/pre_first_token_failure/sandbox_detected_name.txt`
  - `docs/pre_first_token_failure/sandbox_inspect.json`
  - `docs/pre_first_token_failure/sandbox_logs_raw.txt`
  - `docs/pre_first_token_failure/sandbox_watch.log`
  -> `artifacts/runtime_evidence/pre_first_token_failure/`
  Reason: raw evidence belongs in artifacts, not in narrative docs.

- current docs:
  - `docs/SETUP.md`
  - `docs/TROUBLESHOOTING.md`
  - `docs/SECURITY.md`
  -> `docs/current/`

- runtime docs:
  - `docs/runtime_normalization/`
  - `docs/runtime_stabilization/`
  - `docs/pre_first_token_failure/`
  - `docs/runtime_stabilization_contract_v_0.md`
  - `docs/templates/`
  -> `docs/runtime/...`

- architecture docs:
  - `docs/AI_GARAGE_BLUEPRINT.MD.md`
  - `docs/MEMORY_SYSTEM_CONTRACT.md`
  - `docs/Phase_A.md`
  - `docs/ai_garage_library_and_policy_contract_v_0_1.md`
  -> `docs/architecture/`

- research docs:
  - `docs/deep-research-report_#1.md`
  - `docs/deep-research-report_#2.md`
  - `docs/agenticseek_integration_report_2026-03-22.md`
  - `docs/openhands_capabilities_audit_2026-03-22.md`
  - `docs/openhands_handoff_2026-03-22.md`
  - `docs/independent_audit_2026-03-21.md`
  - `docs/stack_audit_2026-03-21.md`
  -> `docs/research/`

- stale contracts/plans:
  - `docs/authoritative_rework_contract_2026-03-21.md`
  - `docs/cleanup_plan_2026-03-21.md`
  - `docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md`
  - `docs/phase_1_consolidated_oh_shop.md`
  - `docs/phase_1_copilot_implementation_plan_next_steps.md`
  - `docs/phase_2_review_pack_artifacts.md`
  - `docs/oh_shop_full_browser_replacement_with_stagehand.md`
  - `docs/ubuntu-25.10-live-server-amd64.iso.torrent`
  -> `docs/archive/`

## Deleted

- `plaintext.txt`
- `compose/openhands_override/__pycache__/`
- `scripts/__pycache__/`
- generated Stagehand cache/dependency directories removed before archiving the copied workspace snapshot:
  - `repos/stagehand(working)/.pnpm-store/`
  - `repos/stagehand(working)/node_modules/`
  - `repos/stagehand(working)/packages/mcp/node_modules/`
  - `repos/stagehand(working)/packages/mcp/dist/`
  - `repos/stagehand(working)/.vscode/`

## Path references updated

- `compose/docker-compose.yml`
  - sandbox workspace bind mount now points at `workspace/`
  - Stagehand MCP build now points at `vendor/stagehand_mcp/`

- `compose/openhands_override/Dockerfile`
  - shared converter overlays now copy from `compat/openhands_sdk_overrides/`

- `compose/agent_server_override/Dockerfile`
  - shared converter overlays now copy from `compat/openhands_sdk_overrides/`

- `docs/current/SETUP.md`
- `docs/current/SECURITY.md`
- `docs/current/TROUBLESHOOTING.md`
- `artifacts/benchmarks/benchmark_runner.py`
- `.gitignore`

## Verification after restructure

- `docker compose -f compose/docker-compose.yml config` passed.
- `./scripts/up.sh` rebuilt successfully from the new `compat/`, `vendor/`, and `workspace/` paths.
- `./scripts/verify.sh` passed layers 1-5 after the rebuilt stack reached steady-state health.
- `python3 scripts/agent_house.py smoke-test-browser-tool ...` passed and wrote `docs/repo_reaudit_restructure/restructure_smoke_check.md`.
