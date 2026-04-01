#!/usr/bin/env sh
set -eu

python3 /app/ops/garage_workspace_bootstrap.py
exec python3 -m uvicorn ops.garage_ledger_service:app --host 0.0.0.0 --port 3032
