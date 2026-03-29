# Normalized Runtime Status After Provider Restore

Date context: 2026-03-29

## Direct verdict

Outcome: **B**

LM Studio is up and the normalized provider boundary is now healthy, but one internal runtime failure still remains.

## What is now proven

- host LM Studio is reachable on `http://localhost:1234` and `http://localhost:1234/v1/models`
- the configured backend model `qwen3-coder-30b-a3b-instruct` is visible
- `openhands-app` can reach LM Studio
- `open-webui` can reach LM Studio
- `stagehand-mcp` can reach LM Studio
- OpenHands live settings still match the normalized config story
- `./scripts/verify.sh` passes Layers 1 through 5 across all cycles

## What is not yet proven

- the canonical browser smoke proof does not complete successfully
- the normalized baseline is therefore not yet fully proof-complete

## Exact remaining blocker

The remaining blocker is an **internal OpenHands/sandbox execution failure after conversation start and before the first LLM/tool event**.

Evidence:
- the smoke run creates the task successfully
- the smoke run creates the sandbox successfully
- the persisted conversation state shows `execution_status` changed from `running` to `error`
- the persisted conversation has no agent `MessageEvent`
- the persisted conversation has no browser `ActionEvent`
- the persisted conversation has no browser `ObservationEvent`
- the app conversation metrics still show zero token usage
- provider-route checks all pass, so this is no longer the old LM Studio outage boundary

## Classification

This remaining blocker is:
- **internal repo/runtime logic**, not external provider availability

Most precise boundary proven in this pass:
- after sandbox boot and config injection
- before first LLM completion or browser-tool call

## Post-run container truth

Command:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Observed result:

```text
NAMES           IMAGE                                     STATUS
openhands-app   oh-shop/openhands:1.5.0-runtime-patched   Up 7 minutes (healthy)
open-webui      ghcr.io/open-webui/open-webui:main        Up 7 minutes (healthy)
stagehand-mcp   oh-stagehand-mcp:0.3.0-runtime-patched    Up 7 minutes (healthy)
```

## Bottom line

The normalized baseline is now:
- rebuildable
- startable
- provider-reachable
- config-aligned

It is **not yet fully proven** because the canonical browser smoke proof still dies at a narrower internal execution boundary inside the OpenHands/sandbox path.
