# TROUBLESHOOTING

> **Current operational troubleshooting only.**
> If another doc tells you to debug Ollama on `11434` or to treat `openhands serve` as the main startup path, that doc is historical.

## First checks

- `docker version`
- `docker ps`
- `curl -sf http://127.0.0.1:1234/v1/models`
- `curl -I http://127.0.0.1:3000`
- `curl -I http://127.0.0.1:3001`
- `curl -I http://127.0.0.1:3002`
- `curl -fsS http://127.0.0.1:3010/health`

## Canonical verifier

Use:

```bash
cd /home/dev/OH_SHOP
./scripts/verify.sh
```

or:

```bash
python3 /home/dev/OH_SHOP/scripts/agent_house.py verify
```

## Notes

- LM Studio must be intentionally running for live provider checks to pass.
- `compose/docker-compose.yml` is the current compose baseline.
- the legacy `compose/openhands.compose.yml` subset has been removed; use `scripts/up.sh` or `compose/docker-compose.yml`.
- a green health check does not prove `oh-browser-mcp` is registered in OpenHands or usable from a fresh session.
