# Script Surface Audit

Date context: 2026-03-29

## Current `scripts/` surface

| Path | Type | Disposition | Why |
| --- | --- | --- | --- |
| `scripts/agent_house.py` | active ops control plane | Keep | This is the real orchestrator. |
| `scripts/up.sh` | active ops wrapper | Keep | Canonical startup shortcut. |
| `scripts/down.sh` | active ops wrapper | Keep | Canonical shutdown shortcut. |
| `scripts/verify.sh` | active ops wrapper | Keep | Canonical verification shortcut. |
| `scripts/verify.py` | active ops wrapper | Keep | Python entry convenience. |
| `scripts/backup_state.sh` | active ops helper | Keep | Legit backup workflow. |
| `scripts/chat_guard.py` | manual repair helper | Keep, flagged | Useful but provisional. |
| `scripts/lmstudio-docker-dnat.sh` | privileged host workaround | Keep, flagged | Manual-only compatibility tool. |

## Removed from `scripts/` surface

| Old path | New path | Why |
| --- | --- | --- |
| `scripts/benchmark_runner.py` | `artifacts/benchmarks/benchmark_runner.py` | It is a benchmark harness, not an ops wrapper. |
| `scripts/__pycache__/...` | deleted | Generated garbage. |

## Script-surface rule

If a file under `scripts/` is not an operator-facing wrapper, control-plane entrypoint, backup helper, or manual repair tool, it does not belong there.
