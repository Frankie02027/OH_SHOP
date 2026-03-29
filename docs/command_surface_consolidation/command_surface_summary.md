# Command Surface Summary

Date context: 2026-03-29

The repo now has one real operator controller:

- `python3 ops/garagectl.py`

That controller owns the normal runtime command surface:
- `up`
- `down`
- `status`
- `logs`
- `verify`
- `backup-state`
- `smoke-test-browser-tool`

The tiny wrapper spam is gone.

What remains outside the controller is manual-only tooling:
- `ops/manual/chat_guard.py`
- `ops/manual/lmstudio-docker-dnat.sh`

That split is intentional:
- controller for normal runtime operations
- manual tools for exceptional repair or privileged host tweaks
