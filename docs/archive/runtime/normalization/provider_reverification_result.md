# Provider Reverification Result

Date context: 2026-03-29

## Scope

This pass re-ran the provider-boundary checks that were previously blocked only because host LM Studio was down.

Authority files used before rerun:
- `docs/runtime_normalization/normalized_runtime_summary.md`
- `docs/runtime_normalization/proof_rerun_result.md`
- `docs/runtime_normalization/runtime_truth_map.md`
- `scripts/agent_house.py`
- `compose/docker-compose.yml`
- `data/openhands/settings.json`

## Host LM Studio checks

Command:

```bash
curl -sS -D - -o /tmp/oh_shop_lm_root.out http://localhost:1234/
sed -n '1,80p' /tmp/oh_shop_lm_root.out
curl -sf http://localhost:1234/v1/models | jq -r '.data[].id'
```

Observed result:

```text
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: application/json; charset=utf-8
Content-Length: 50
ETag: W/"32-e6rgb5BPJ+PUVQosDi3B/Ob1epE"
Date: Sun, 29 Mar 2026 16:38:51 GMT
Connection: keep-alive
Keep-Alive: timeout=5

{"error":"Unexpected endpoint or method. (GET /)"}

nebius-swe-rebench-openhands-qwen3-30b-a3b
qwen/qwen3.5-35b-a3b
qwen/qwen3-vl-8b
qwen3-coder-30b-a3b-instruct
qwen/qwen3.5-9b
mistralai/devstral-small-2-2512
text-embedding-nomic-embed-text-v1.5
```

Interpretation:
- `http://localhost:1234/` is alive and responding from LM Studio.
- `http://localhost:1234/v1/models` is healthy.
- The configured backend model `qwen3-coder-30b-a3b-instruct` is visible.

## Container route checks

### OpenHands container

Command:

```bash
docker exec openhands-app python -c "import json,urllib.request; payload=json.load(urllib.request.urlopen('http://host.docker.internal:1234/v1/models', timeout=10)); print('status=ok'); print('models=' + ','.join(item['id'] for item in payload.get('data', [])))"
```

Observed result:

```text
status=ok
models=nebius-swe-rebench-openhands-qwen3-30b-a3b,qwen/qwen3.5-35b-a3b,qwen/qwen3-vl-8b,qwen3-coder-30b-a3b-instruct,qwen/qwen3.5-9b,mistralai/devstral-small-2-2512,text-embedding-nomic-embed-text-v1.5
```

### OpenWebUI container

Command:

```bash
docker exec open-webui python -c "import json,urllib.request; payload=json.load(urllib.request.urlopen('http://host.docker.internal:1234/v1/models', timeout=10)); print('status=ok'); print('models=' + ','.join(item['id'] for item in payload.get('data', [])))"
```

Observed result:

```text
status=ok
models=nebius-swe-rebench-openhands-qwen3-30b-a3b,qwen/qwen3.5-35b-a3b,qwen/qwen3-vl-8b,qwen3-coder-30b-a3b-instruct,qwen/qwen3.5-9b,mistralai/devstral-small-2-2512,text-embedding-nomic-embed-text-v1.5
```

### Stagehand MCP container

Command:

```bash
docker exec stagehand-mcp node -e "fetch('http://host.docker.internal:1234/v1/models').then(async r => { const j = await r.json(); console.log('status=' + r.status); console.log('models=' + j.data.map(x => x.id).join(',')); }).catch(err => { console.error(err); process.exit(1); })"
```

Observed result:

```text
status=200
models=nebius-swe-rebench-openhands-qwen3-30b-a3b,qwen/qwen3.5-35b-a3b,qwen/qwen3-vl-8b,qwen3-coder-30b-a3b-instruct,qwen/qwen3.5-9b,mistralai/devstral-small-2-2512,text-embedding-nomic-embed-text-v1.5
```

Interpretation:
- All three core runtime surfaces can reach LM Studio through the canonical container route `http://host.docker.internal:1234/v1`.

## OpenHands live settings alignment

Persisted settings authority:
- `data/openhands/settings.json`

Live settings check command:

```bash
curl -sf http://127.0.0.1:3000/api/settings | jq '{llm_model, llm_base_url, mcp_config}'
```

Observed result:

```json
{
  "llm_model": "openai/qwen3-coder-30b-a3b-instruct",
  "llm_base_url": "http://host.docker.internal:1234/v1",
  "mcp_config": {
    "sse_servers": [],
    "stdio_servers": [],
    "shttp_servers": [
      {
        "url": "http://host.docker.internal:3020/mcp",
        "api_key": null,
        "timeout": 60
      }
    ]
  }
}
```

Alignment result:
- live `llm_model` matches persisted `openai/qwen3-coder-30b-a3b-instruct`
- live `llm_base_url` matches persisted `http://host.docker.internal:1234/v1`
- live MCP URL matches persisted `http://host.docker.internal:3020/mcp`

## Sandbox-path note

The canonical smoke proof created a sandbox successfully, but the smoke run later failed before any tool action or final reply.

What can be proven from this pass:
- the sandbox path exists and starts
- the sandbox received the canonical provider config and MCP config
- the core provider-route failure from the previous rerun is gone

What was not independently re-proven as a standalone direct command:
- a manual `curl` from the transient smoke sandbox to LM Studio after task start

Reason:
- the canonical smoke harness auto-cleans the sandbox after completion
- the rerun already isolated the remaining failure to a later internal execution boundary, not the original provider-route boundary

## Verdict

Provider restoration is successful.

The previously missing provider checks now pass on:
- host
- `openhands-app`
- `open-webui`
- `stagehand-mcp`

The configured backend model is visible.
The normalized provider/config story is still aligned.
