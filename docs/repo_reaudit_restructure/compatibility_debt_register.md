# Compatibility Debt Register

Date context: 2026-03-29

| Path | What it does | Why it still exists | Runtime dependency | Fate |
| --- | --- | --- | --- | --- |
| `compat/openhands_sdk_overrides/fn_call_converter.py` | overrides OpenHands SDK converter behavior | local LM Studio/OpenHands tool-calling compatibility | copied into app and sandbox images | Keep for now, later replace with pinned upstream fix or maintained fork |
| `compat/openhands_sdk_overrides/fn_call_converter_v0.py` | paired legacy converter override | same reason as above | copied into app and sandbox images | Keep for now, later replace |
| `compose/openhands_override/apply_runtime_patches.py` | applies OpenHands app patch set at build time | current runtime still depends on prompt/filter/live-status mutations | OpenHands app image | Keep, but it remains patch debt |
| `compose/agent_server_override/Dockerfile` | repacks sandbox from upstream binary image into importable Python runtime | current sandbox override strategy still depends on it | sandbox image family | Keep until sandbox source build path is made honest |
| `vendor/stagehand_mcp/src/server.ts` | hosts MCP SHTTP server and includes schema/model-response shims | Stagehand + LM Studio still need compatibility handling | stagehand-mcp service | Keep, but narrow later |
| `scripts/chat_guard.py` | reconciles stale chat rows / orphan containers | some runtime cleanup remains manual/provisional | optional manual or compose sidecar usage | Keep as manual repair tool, not architecture |
| `scripts/lmstudio-docker-dnat.sh` | installs privileged host routing workaround | useful only on hosts where `host.docker.internal` is not enough | manual host ops only | Keep manual-only; never treat as baseline |
| `workspace/.openhands_instructions` | hidden workspace-root behavior file | possible OpenHands prompt-loading behavior still unclear | any sandboxed workspace run | Keep but review later; it is governance debt |

## Rules after this pass

- New compatibility shims belong under `compat/` or inside the specific extracted vendor slice that truly needs them.
- Do not hide compatibility edits in normal-looking runtime folders without calling them out.
- If a shim becomes unnecessary, remove it from the debt register instead of letting it rot silently.
