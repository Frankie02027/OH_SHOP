# Wrapper Removal Log

Date context: 2026-03-29

## Removed wrapper files

- `scripts/up.sh`
  Reason: forwarded directly into the controller.

- `scripts/down.sh`
  Reason: forwarded directly into the controller.

- `scripts/verify.sh`
  Reason: forwarded directly into the controller.

- `scripts/verify.py`
  Reason: forwarded directly into the controller.

## Merged into controller

- `scripts/agent_house.py`
  -> `ops/garagectl.py`
  Reason: promoted to the one real control entrypoint.

- `scripts/backup_state.sh`
  -> `ops/garagectl.py backup-state`
  Reason: small enough to belong on the controller.

## Rehomed as manual tools

- `scripts/chat_guard.py`
  -> `ops/manual/chat_guard.py`

- `scripts/lmstudio-docker-dnat.sh`
  -> `ops/manual/lmstudio-docker-dnat.sh`
