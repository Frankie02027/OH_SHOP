#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_ROOT="$ROOT/artifacts/backups"
STAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$BACKUP_ROOT/$STAMP"

mkdir -p "$DEST"

copy_if_exists() {
  local path="$1"
  if [ -e "$path" ]; then
    cp -a "$path" "$DEST/"
  fi
}

copy_if_exists "$ROOT/data/openhands"
copy_if_exists "$ROOT/compose/docker-compose.yml"
copy_if_exists "$ROOT/compose/openhands.compose.yml"
copy_if_exists "$HOME/.lmstudio/.internal/http-server-config.json"
copy_if_exists "$HOME/.lmstudio/settings.json"
copy_if_exists "$HOME/.lmstudio/.internal/app-install-location.json"

cat >"$DEST/README.txt" <<EOF
OH_SHOP state backup
Created: $STAMP

Included when present:
- data/openhands
- compose/docker-compose.yml
- compose/openhands.compose.yml
- LM Studio config files
EOF

printf 'Backup created at %s\n' "$DEST"
