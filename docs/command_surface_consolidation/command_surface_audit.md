# Command Surface Audit

Date context: 2026-03-29

| Path | Classification | Reason |
| --- | --- | --- |
| `scripts/agent_house.py` | `MERGE_INTO_CONTROLLER` | Real controller logic, but wrong surface name/location after repo restructure. |
| `scripts/up.sh` | `DELETE` | Tiny wrapper that only forwarded `up`. |
| `scripts/down.sh` | `DELETE` | Tiny wrapper that only forwarded `down`. |
| `scripts/verify.sh` | `DELETE` | Tiny wrapper that only forwarded `verify`. |
| `scripts/verify.py` | `DELETE` | Tiny wrapper that only forwarded `verify`. |
| `scripts/backup_state.sh` | `MERGE_INTO_CONTROLLER` | Real operator behavior, but small enough to live as a controller subcommand. |
| `scripts/chat_guard.py` | `KEEP_AS_MANUAL_TOOL` | Real manual repair tool, not baseline controller surface. |
| `scripts/lmstudio-docker-dnat.sh` | `KEEP_AS_MANUAL_TOOL` | Privileged host helper, not baseline controller surface. |

## Final ruling

- core controller: `ops/garagectl.py`
- separate manual tools:
  - `ops/manual/chat_guard.py`
  - `ops/manual/lmstudio-docker-dnat.sh`

The wrapper files were noise, not architecture.
