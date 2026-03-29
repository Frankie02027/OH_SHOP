# Repo Restructure Summary

Date context: 2026-03-29

The repo now has an honest surface.

- `compose/` is the live runtime/build surface.
- `ops/` is the live command and manual-ops surface.
- `compat/` is explicit compatibility debt.
- `vendor/` holds the active Stagehand MCP slice.
- `workspace/` is the only sandbox-exposed work tree.
- `docs/current/` is the operator doc surface.
- `archive/` holds dead, future-only, or reference-only code that should not pretend to be live.

The biggest cleanup was removing the overloaded `repos/` mess. It used to mix a workspace root, copied upstream repos, toy junk, and the active browser vendor tree in one misleading place. That is gone.

The canonical runtime survived the restructure:
- `python3 ops/garagectl.py up` rebuilt successfully
- `python3 ops/garagectl.py verify` passed layers 1-5 in steady state
- `python3 ops/garagectl.py smoke-test-browser-tool ...` passed and wrote `docs/repo_reaudit_restructure/restructure_smoke_check.md`

What still remains as honest debt:
- OpenHands patching is still real patch debt
- Stagehand MCP still contains LM Studio compatibility shims
- `chat_guard.py`, `lmstudio-docker-dnat.sh`, and `workspace/.openhands_instructions` remain special-case tools/policy debt
