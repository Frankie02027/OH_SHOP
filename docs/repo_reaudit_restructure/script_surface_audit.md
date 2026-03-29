# Script Surface Audit

Date context: 2026-03-29

## Final command/manual surface

| Path | Type | Disposition | Why |
| --- | --- | --- | --- |
| `ops/garagectl.py` | controller | Keep | Single operator entrypoint with subcommands. |
| `ops/manual/chat_guard.py` | manual repair helper | Keep, flagged | Useful but provisional. |
| `ops/manual/lmstudio-docker-dnat.sh` | privileged host workaround | Keep, flagged | Manual-only compatibility tool. |

## Removed wrapper clutter

| Old path | New path | Why |
| --- | --- | --- |
| `scripts/agent_house.py` | `ops/garagectl.py` | Promoted to the single real controller. |
| `scripts/up.sh` | removed | Tiny forwarder into the controller. |
| `scripts/down.sh` | removed | Tiny forwarder into the controller. |
| `scripts/verify.sh` | removed | Tiny forwarder into the controller. |
| `scripts/verify.py` | removed | Tiny forwarder into the controller. |
| `scripts/backup_state.sh` | merged into `ops/garagectl.py backup-state` | Backup belongs on the controller command map. |
| `scripts/chat_guard.py` | `ops/manual/chat_guard.py` | Manual repair tool, not controller surface. |
| `scripts/lmstudio-docker-dnat.sh` | `ops/manual/lmstudio-docker-dnat.sh` | Manual privileged helper, not controller surface. |
| `scripts/benchmark_runner.py` | `artifacts/benchmarks/benchmark_runner.py` | It is a benchmark harness, not an ops wrapper. |

## Rule after this pass

If an operator command only forwards into the controller, it does not deserve its own file.
