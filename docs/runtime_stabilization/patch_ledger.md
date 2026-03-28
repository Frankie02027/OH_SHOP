# Runtime Patch Ledger

Date context: 2026-03-27

This ledger records the active and competing patch layers affecting the current runtime.

## Ledger entries

| Path | Component touched | Upstream/base target | Category | Exact purpose | Known symptom/bug addressed | Clearly active? | Duplicated elsewhere? | Risk | Proposed fate | Proof/test that justifies keeping it |
|---|---|---|---|---|---|---|---|---|---|---|
| `compose/openhands_override/Dockerfile` | OpenHands app image | `docker.openhands.dev/openhands/openhands:latest` | Dockerfile inline patch + vendored override | Overlays patched converters, runs routing patch script, forces `native_tool_calling` rule, forces default tools inclusion | Local LM Studio tool-calling compatibility; no-repo browser/tool behavior | Yes | Yes; overlaps with `scripts/patch_openhands_tool_call_mode.py` and vendored converter copies in agent-server override | High | Rewrite | Build OpenHands image, confirm tool-calling works, confirm no blind-patch miss, run browser proof task |
| `compose/agent_server_override/Dockerfile` | agent-server sandbox image | `ghcr.io/openhands/agent-server:61470a1-python` plus pip packages `1.11.4` | Dockerfile override | Replaces binary entrypoint, installs Python packages, overlays patched converter files | Need importable Python source and patched SDK behavior in sandbox runtime | Yes | Yes; converter patches duplicate OpenHands override copies | High | Rewrite | Build image and verify installed package versions and expected converter behavior inside sandbox |
| `scripts/patch_openhands_external_resource_routing.py` | OpenHands prompts and app-server conversation flow | OpenHands app source inside image | Patch script | Biases no-repo conversations toward external resource browsing, patches skill loading, MCP filtering, and title callback behavior | External resource requests being misrouted to local workspace; callback noise | Yes, because `compose/openhands_override/Dockerfile` runs it | Partially; default-tools behavior is later contradicted by inline Dockerfile patch | High | Merge | Compare built image source against expected patches, then run a no-repo external-resource task |
| `scripts/patch_openhands_tool_call_mode.py` | OpenHands LLM/tool converter code | OpenHands app source inside image | Patch script | Adds `native_tool_calling=False` for `openhands-lm` and patches converter parsing | Local model malformed tool markup and parameter issues | No clear active build path | Yes; overlaps heavily with `compose/openhands_override/Dockerfile` and vendored converter files | Medium | Quarantine | Only keep if some active build path still executes it; currently no proof |
| `scripts/chat_guard.py` | OpenHands runtime DB and sandbox containers | `data/openhands/openhands.db` plus Docker runtime | Runtime janitor tool | Deletes orphan callback/start-task rows and removes stale `oh-agent-server-*` containers | Stale transient chat rows and leaked sandbox containers | Yes as a tool; no as default architecture | No exact duplicate, but compose embeds it as optional service | Medium | Keep | Run against known stale DB state and confirm it only removes transient orphan records |
| `scripts/lmstudio-docker-dnat.sh` | Host networking | Linux sysctls and iptables | Host networking helper | Forwards bridged Docker traffic to host LM Studio on `127.0.0.1:1234` | Host model provider not reachable from containers in some host-network configurations | Possibly host-specific; not proven required in current compose path | No | Medium | Keep | Demonstrate a host where `host.docker.internal` is insufficient and DNAT is required |
| `compose/openhands_override/vendor_sdk/fn_call_converter.py` | OpenHands SDK converter in app image | `/app/.venv/.../openhands/sdk/llm/mixins/fn_call_converter.py` | Vendored file override | Normalizes malformed tool markup, ignores `security_risk`/`summary`, loosens parsing | Local model non-standard function-call markup | Yes | Yes; identical to agent-server override copy | High | Merge | Confirm converter behavior is still required via failing/passing tool-call fixture |
| `compose/openhands_override/vendor_sdk/fn_call_converter_v0.py` | OpenHands legacy converter in app image | `/app/openhands/llm/fn_call_converter.py` | Vendored file override | Same compatibility family for V0 path | Same | Yes | Yes; same compatibility family exists in agent-server override | High | Merge | Same as above |
| `compose/agent_server_override/vendor_sdk/fn_call_converter.py` | SDK converter in sandbox image | `/usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter.py` | Vendored file override | Keeps sandbox-side SDK converter behavior aligned with patched app behavior | Tool-call parsing mismatch between app and sandbox | Yes | Yes; identical to OpenHands override copy | High | Merge | Confirm sandbox code path actually uses these functions during proof task |
| `compose/agent_server_override/vendor_sdk/fn_call_converter_v0.py` | V0 converter in sandbox image | `/usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter_v0.py` | Vendored file override | Same compatibility family for sandbox V0 path | Same | Yes | Yes; same compatibility family exists in OpenHands override | High | Merge | Same as above |
| `compose/agent_server_override/vendor_sdk/vendor_sdk/fn_call_converter.py` | Duplicate vendored SDK file | None in active Dockerfile | Duplicate vendored file | Shadow copy of active override file | None; this is clutter | No | Yes; exact duplicate family | Low | Delete after quarantine | No active Dockerfile should reference it |
| `compose/agent_server_override/vendor_sdk/vendor_sdk/fn_call_converter_v0.py` | Duplicate vendored SDK file | None in active Dockerfile | Duplicate vendored file | Shadow copy of active override file | None; this is clutter | No | Yes; exact duplicate family | Low | Delete after quarantine | No active Dockerfile should reference it |
| `repos/stagehand(working)/packages/mcp/src/server.ts` | Stagehand MCP server | local Stagehand MCP service | Local service compatibility shim | Injects `strict=true`, strips unsupported schema fields, rewrites `elementId`, resolves model name, hosts MCP | LM Studio JSON schema incompatibilities and Stagehand/LM Studio response-format issues | Yes | No exact duplicate in active runtime | High | Rewrite | Run structured extract/act calls and confirm they fail without shim but pass with it |
| `bridge/model_router/router.ts` | Off-path LM Studio proxy | host LM Studio | Local service compatibility shim | Model hot-swap proxy for text vs VL lanes | One-model-on-GPU pressure and vision-to-text routing | No current runtime path | No active duplicate, but conceptually superseded by direct LM Studio route | Medium | Quarantine | Only revive if compose/runtime explicitly re-adopts it |

## Cross-entry duplication findings

- `compose/openhands_override/vendor_sdk/fn_call_converter.py` and `compose/agent_server_override/vendor_sdk/fn_call_converter.py` are identical.
- `compose/openhands_override/vendor_sdk/fn_call_converter_v0.py` and `compose/agent_server_override/vendor_sdk/fn_call_converter_v0.py` are the same compatibility family.
- `scripts/patch_openhands_tool_call_mode.py` duplicates the active OpenHands override strategy and appears superseded.
- `scripts/patch_openhands_external_resource_routing.py` and the inline patch inside `compose/openhands_override/Dockerfile` still disagree on default-tools behavior. The Dockerfile inline patch wins because it runs after the script.

## High-risk patch truths

1. The OpenHands app image still patches a floating upstream `latest` image.
2. The agent-server image still mixes a `61470a1-python` base family with `1.11.4` Python packages.
3. Stagehand compatibility still depends on local `server.ts` shims instead of a clean upstream-supported integration.
4. `chat-guard` is operationally useful but is still a janitor hack, not architecture.

## Phase 1 applied stabilization changes

These were minimal contract-aligned changes made after the baseline, config, patch, and version artifacts existed.

| Path | Phase 1 change | Why it was safe in this phase | Proof/evidence |
|---|---|---|---|
| `scripts/agent_house.py` | Changed `EXPECTED_MCP_URL` to `http://host.docker.internal:3020/mcp` | It reconciled the verifier with persisted OpenHands settings and the actual host-published `stagehand-mcp` path | `./scripts/verify.sh` now passes the MCP URL assertion |
| `scripts/agent_house.py` | Changed the agent-server build tag to `oh-shop/agent-server:1.11.4-runtime-patched` | It removed the lie that the built image was a `61470a1` family when the installed packages are `1.11.4` | `docker images` and `docker run ... importlib.metadata ...` confirm the new honest tag |
| `scripts/agent_house.py` | Reworded Layer 4 from strong readiness language to weak endpoint reachability language | It stopped overstating what `/healthz` proves | `./scripts/verify.sh` still passes, but the wording no longer lies |
| `scripts/agent_house.py` | Replaced a `curl`-inside-container assumption with a Node `fetch()` probe for Stagehand's provider route | The `stagehand-mcp` image does not ship `curl`; the old verifier was wrong | First verify run failed on missing `curl`; second verify run passed after this fix |
| `compose/docker-compose.yml` | Renamed the OpenHands app image to `oh-shop/openhands:1.5.0-runtime-patched` | It aligned the local tag with the runtime version actually reported by the built image | `docker run --rm --entrypoint python oh-shop/openhands:1.5.0-runtime-patched ...` prints `1.5.0` |
| `compose/docker-compose.yml` | Renamed `AGENT_SERVER_IMAGE_TAG` to `1.11.4-runtime-patched` | It aligned OpenHands sandbox-launch config with the actually built local image | `docker ps` and sandbox proof runs used the new tag family |
| `compose/docker-compose.yml` | Set `STAGEHAND_MODEL=${STAGEHAND_MODEL:-qwen3-coder-30b-a3b-instruct}` | It removed the blank default that previously created split or implicit model-selection behavior | `stagehand-mcp` boots and the browser proof reaches Stagehand tools |
| `repos/stagehand(working)/packages/mcp/src/server.ts` | Changed `browserbase_stagehand_agent` to use `getStagehandModelName()` | It removed the special-case broken path that used raw blank `MODEL_NAME` | Fresh proof runs show Stagehand tools executing instead of dying earlier on model selection |
| `data/openhands/settings.json` | Changed `llm_model` to `openai/qwen3-coder-30b-a3b-instruct` | It aligned persisted OpenHands state with a model family the host provider actually exposes | `curl -sf http://127.0.0.1:3000/api/settings` shows the new value live |
| `docs/SETUP.md` | Rewrote the runtime setup doc to match the current stack | It removed the stale runtime claim that `SearxNG` and `oh-browser-mcp` are current | The doc now names `LM Studio + OpenHands + OpenWebUI + Stagehand MCP` as current |
| `docs/authoritative_rework_contract_2026-03-21.md` | Added a top banner marking it historical/stale for runtime authority | It neutralized a former authority doc without destroying evidence | The file now self-identifies as historical and non-authoritative for current runtime work |
| `scripts/__pycache__/agent_house.cpython-313.pyc` | Removed tracked generated bytecode | It was generated noise, not a runtime authority path | The file is deleted from the worktree |

## Immediate stabilization implications

- The repo now has fewer active lies about:
  - which MCP URL wins
  - which Stagehand model-selection rule wins
  - which OpenHands and agent-server tags are supposed to mean what
  - what the setup doc claims is current
- The patch story is still too fragmented for comfort.
- The safe next direction remains:
  - one OpenHands app override path
  - one agent-server override path
  - one explicit Stagehand compatibility path
  - removal of superseded scripts and duplicate vendored trees after quarantine acceptance
