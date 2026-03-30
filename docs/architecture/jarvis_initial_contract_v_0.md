# Jarvis Initial Contract v0

> **Historical forwarder only.**
> This path previously carried live Jarvis authority content under a misleading filename.
> The active Jarvis authority now lives at [JARVIS_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_1.md).
**Action Report**

I cleaned the authority surface without touching runtime behavior.

Files changed:
- Created the real Robin authority file at [ROBIN_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_1.md).
- Rewrote [robin_initial_contract_v_0.md](/home/dev/OH_SHOP/docs/architecture/robin_initial_contract_v_0.md) into a historical forwarder.
- Rewrote [jarvis_initial_contract_v_0.md](/home/dev/OH_SHOP/docs/architecture/jarvis_initial_contract_v_0.md) into a historical forwarder.
- Updated [ROBIN_MASTER_CONTRACT_MERGE_NOTES_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_MERGE_NOTES_v_0_1.md) so it no longer silently points at a missing authority target.
- Updated [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md) so it points to the actual current runtime authority surface and to the new runtime archive.
- Rewrote [fresh_session_mcp_proof_run.md](/home/dev/OH_SHOP/docs/runtime/templates/fresh_session_mcp_proof_run.md) to use the current Stagehand MCP registration and browser-proof prompt.
- Added strong historical framing to [MEMORY_SYSTEM_CONTRACT.md](/home/dev/OH_SHOP/docs/architecture/MEMORY_SYSTEM_CONTRACT.md).
- Fixed the stale active-setup pointer in [Phase_A.md](/home/dev/OH_SHOP/docs/architecture/Phase_A.md).
- Updated [.gitignore](/home/dev/OH_SHOP/.gitignore) so `docs/archive/` is trackable even though the root `archive/` tree stays ignored.

Files moved to quarantine/archive:
- I quarantined the stale runtime phase artifacts under [docs/archive/runtime](/home/dev/OH_SHOP/docs/archive/runtime).
- That includes the old normalization set now under [docs/archive/runtime/normalization](/home/dev/OH_SHOP/docs/archive/runtime/normalization).
- That includes the old stabilization set now under [docs/archive/runtime/stabilization](/home/dev/OH_SHOP/docs/archive/runtime/stabilization).
- That includes the old pre-first-token investigation set now under [docs/archive/runtime/investigations/pre_first_token_failure](/home/dev/OH_SHOP/docs/archive/runtime/investigations/pre_first_token_failure).
- I added [README.md](/home/dev/OH_SHOP/docs/archive/runtime/README.md) there so the archive identifies itself as historical evidence, not current authority.

Files intentionally left alone:
- [JARVIS_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_1.md)
- [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md)
- [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md)
- [master_intent_brief.md](/home/dev/OH_SHOP/docs/runtime/stabilization/master_intent_brief.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)
- [SECURITY.md](/home/dev/OH_SHOP/docs/current/SECURITY.md)

Debug-first / no-delete-yet:
- [server.ts](/home/dev/OH_SHOP/vendor/stagehand_mcp/src/server.ts)
- [package.json](/home/dev/OH_SHOP/vendor/stagehand_mcp/package.json)
- [Dockerfile](/home/dev/OH_SHOP/vendor/stagehand_mcp/Dockerfile)
- [apply_runtime_patches.py](/home/dev/OH_SHOP/compose/openhands_override/apply_runtime_patches.py)
- [Dockerfile](/home/dev/OH_SHOP/compose/agent_server_override/Dockerfile)
- [fn_call_converter.py](/home/dev/OH_SHOP/compat/openhands_sdk_overrides/fn_call_converter.py)
- [fn_call_converter_v0.py](/home/dev/OH_SHOP/compat/openhands_sdk_overrides/fn_call_converter_v0.py)
- [garagectl.py](/home/dev/OH_SHOP/ops/garagectl.py)
- [chat_guard.py](/home/dev/OH_SHOP/ops/manual/chat_guard.py)
- [lmstudio-docker-dnat.sh](/home/dev/OH_SHOP/ops/manual/lmstudio-docker-dnat.sh)

**Repo-State Summary**

What is now the Robin authority file:
- [ROBIN_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_1.md)

What is now the Jarvis authority file:
- [JARVIS_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_1.md)

What docs are current runtime truth:
- [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)
- [SECURITY.md](/home/dev/OH_SHOP/docs/current/SECURITY.md)
- [README.md](/home/dev/OH_SHOP/ops/README.md)
- [docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml)
- [fresh_session_mcp_proof_run.md](/home/dev/OH_SHOP/docs/runtime/templates/fresh_session_mcp_proof_run.md)

What docs are historical only:
- everything quarantined under [docs/archive/runtime](/home/dev/OH_SHOP/docs/archive/runtime)
- the old forwarder paths [jarvis_initial_contract_v_0.md](/home/dev/OH_SHOP/docs/architecture/jarvis_initial_contract_v_0.md) and [robin_initial_contract_v_0.md](/home/dev/OH_SHOP/docs/architecture/robin_initial_contract_v_0.md)
- the older proposal/log docs [MEMORY_SYSTEM_CONTRACT.md](/home/dev/OH_SHOP/docs/architecture/MEMORY_SYSTEM_CONTRACT.md) and [Phase_A.md](/home/dev/OH_SHOP/docs/architecture/Phase_A.md)

Files I refused to delete yet and why:
- the runtime bridge, patch, and compat files above remain because they are implementation debt, not safe blind-delete targets
- [master_intent_brief.md](/home/dev/OH_SHOP/docs/runtime/stabilization/master_intent_brief.md) stayed live because it is still clean architecture intent, not stale runtime fiction

Remaining unresolved issues:
- [MEMORY_SYSTEM_CONTRACT.md](/home/dev/OH_SHOP/docs/architecture/MEMORY_SYSTEM_CONTRACT.md) and [Phase_A.md](/home/dev/OH_SHOP/docs/architecture/Phase_A.md) are now clearly labeled, but they still live in `docs/architecture/`; a stricter later pass could archive them fully.
- The archived runtime files are now under `docs/archive/runtime/`, and because they were moved there from tracked paths, you should commit the archive additions together with the deletions so the quarantine is preserved cleanly.
- I did not debug or trim any runtime patch/compat code in this pass.

**Verification**

Required checks:
- `git branch --show-current` -> `master`
- stale runtime truth grep on `docs/architecture docs/runtime docs/current ops compat compose vendor` -> **no matches**
- authority/title scan now shows:
  - [ROBIN_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_1.md): `# ROBIN Master Contract v0.1`
  - [robin_initial_contract_v_0.md](/home/dev/OH_SHOP/docs/architecture/robin_initial_contract_v_0.md): `# Robin Initial Contract v0`
  - [jarvis_initial_contract_v_0.md](/home/dev/OH_SHOP/docs/architecture/jarvis_initial_contract_v_0.md): `# Jarvis Initial Contract v0`
- the direct authority target check now shows [ROBIN_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_1.md) exists and the old Robin/Jarvis initial paths are forwarders, not fake live authority
- `git diff --stat` currently shows the expected live-surface cleanup plus runtime-doc deletions from `docs/runtime/*`; `git status --short` also shows the new archive tree under `docs/archive/` and the new Robin master file waiting to be committed

This pass finished the authority cleanup target: the repo no longer claims deleted `scripts/*` and old Stagehand paths as live current truth in the current-facing surfaces, and the Robin/Jarvis authority paths are no longer ambiguous.
## Status

- classification: stale duplicate-authority artifact
- active authority replacement: `docs/architecture/JARVIS_MASTER_CONTRACT_v_0_1.md`
- reason retained: preserve old references without leaving a fake competing authority on disk

Use the Jarvis master contract for current role truth.
