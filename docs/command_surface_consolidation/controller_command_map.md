# Controller Command Map

Date context: 2026-03-29

## Final controller

- `python3 ops/garagectl.py`

## Final subcommands

- `up`
- `down`
- `status`
- `logs`
- `verify`
- `backup-state`
- `cleanup-sandboxes`
- `capture-proof-context`
- `smoke-test-browser-tool`
- `reconcile-chats`
- `monitor-chats`

## Old -> new mapping

| Old command | New command |
| --- | --- |
| `./scripts/up.sh` | `python3 ops/garagectl.py up` |
| `./scripts/down.sh` | `python3 ops/garagectl.py down` |
| `./scripts/verify.sh` | `python3 ops/garagectl.py verify` |
| `python3 scripts/verify.py` | `python3 ops/garagectl.py verify` |
| `python3 scripts/agent_house.py up` | `python3 ops/garagectl.py up` |
| `python3 scripts/agent_house.py down` | `python3 ops/garagectl.py down` |
| `python3 scripts/agent_house.py verify` | `python3 ops/garagectl.py verify` |
| `python3 scripts/agent_house.py logs` | `python3 ops/garagectl.py logs` |
| `python3 scripts/agent_house.py smoke-test-browser-tool` | `python3 ops/garagectl.py smoke-test-browser-tool` |
| `bash scripts/backup_state.sh` | `python3 ops/garagectl.py backup-state` |
| `python3 scripts/chat_guard.py` | `python3 ops/garagectl.py reconcile-chats` or `python3 ops/manual/chat_guard.py` |

