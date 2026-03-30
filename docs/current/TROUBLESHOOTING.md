# TROUBLESHOOTING

> **Current operational troubleshooting only.**
> If another doc tells you to debug Ollama on `11434` or to treat `openhands serve` as the main startup path, that doc is historical.

## First checks

- `docker version`
- `docker ps`
- `readlink -f "$(command -v lmstudio)"`
- `curl -sf http://127.0.0.1:1234/v1/models`
- `curl -I http://127.0.0.1:3000`
- `curl -I http://127.0.0.1:3001`
- `curl -fsS http://127.0.0.1:3020/healthz`

## Canonical verifier

Use:

```bash
cd /home/dev/OH_SHOP
python3 ops/garagectl.py verify
```

or:

```bash
python3 /home/dev/OH_SHOP/ops/garagectl.py verify
```

## Notes

- LM Studio must be intentionally running for live provider checks to pass.
- the configured model ID must also be visible in `curl -sf http://127.0.0.1:1234/v1/models`; if the server is up but the configured model string is absent, layer 5 of the verifier and the browser smoke can still fail.
- the authoritative host launcher is `/usr/bin/lm-studio`
- `lmstudio` should resolve to `/usr/bin/lm-studio`, not the legacy AppImage path under `/opt/lmstudio/`
- `compose/docker-compose.yml` is the current compose baseline.
- the legacy `compose/openhands.compose.yml` subset has been removed; use `python3 ops/garagectl.py up` or `compose/docker-compose.yml`.
- a green health check does not prove `stagehand-mcp` is registered in OpenHands or usable from a fresh session.
