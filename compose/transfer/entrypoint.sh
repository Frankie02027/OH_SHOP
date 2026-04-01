#!/usr/bin/env sh
set -eu

python3 -m ops.garage_workspace_bootstrap
exec python3 -m uvicorn ops.garage_transfer_service:app --host 0.0.0.0 --port 3033
