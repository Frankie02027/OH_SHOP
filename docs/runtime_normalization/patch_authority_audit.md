# Patch Authority Audit

Date context: 2026-03-29

This audit records the currently winning patch layers before normalization changes are applied.

## Active patch layers that currently win

| Path | Target | What it changes | Current winner status | Problem |
|---|---|---|---|---|
| `compose/openhands_override/Dockerfile` | OpenHands app image | copies patched converters, runs external-resource patch script, applies two inline string patches | Active | Patch authority is split between Dockerfile inline mutations and an external helper script. |
| `scripts/patch_openhands_external_resource_routing.py` | OpenHands prompt/app-server flow inside the image | external-resource prompt bias, no-repo suffix, MCP filter, skill filter, title callback suppression, selected-repository plumb-through | Active because Dockerfile runs it | Default-tools behavior in this script is later contradicted by the Dockerfile inline patch. |
| `compose/openhands_override/vendor_sdk/fn_call_converter.py` | app image SDK converter | normalizes local-model function-call markup | Active | Duplicated elsewhere. |
| `compose/openhands_override/vendor_sdk/fn_call_converter_v0.py` | app image legacy converter path | same compatibility family for V0 path | Active | Duplicated elsewhere. |
| `compose/agent_server_override/Dockerfile` | sandbox image | installs top-level Python packages and overlays patched converter files | Active | Sandbox patch authority depends on separate duplicated vendor files. |
| `compose/agent_server_override/vendor_sdk/fn_call_converter.py` | sandbox SDK converter | same converter compatibility patch as app image | Active | Exact duplicate of the app-image override. |
| `compose/agent_server_override/vendor_sdk/fn_call_converter_v0.py` | sandbox V0 converter | same compatibility family | Active | Duplicate family. |
| `repos/stagehand(working)/packages/mcp/src/server.ts` | Stagehand MCP | schema strictness injection, schema cleanup, bracketed `elementId` fixes, model-name resolution, health endpoint, MCP SHTTP server | Active | It is a necessary shim today, but it is one large compatibility blob. |

## Patch layers present but not winning

| Path | Status | Why it loses | Risk if left in place |
|---|---|---|---|
| `scripts/patch_openhands_tool_call_mode.py` | non-winning | no active build path runs it | It keeps a second believable OpenHands tool-call patch story alive. |
| `compose/agent_server_override/vendor_sdk/vendor_sdk/fn_call_converter.py` | non-winning | no active Dockerfile path references it | Pure duplicate clutter. |
| `compose/agent_server_override/vendor_sdk/vendor_sdk/fn_call_converter_v0.py` | non-winning | no active Dockerfile path references it | Pure duplicate clutter. |
| `repos/stagehand(working)/packages/mcp/src/server.ts.bak` | non-winning | active build copies `src/server.ts`, not `.bak` | Shadow implementation beside the live file. |

## What actually wins in practice

### OpenHands app

Effective winner order before normalization:

1. base image files from `docker.openhands.dev/openhands/openhands:latest`
2. converter overrides copied from `compose/openhands_override/vendor_sdk/`
3. `scripts/patch_openhands_external_resource_routing.py`
4. inline Dockerfile patch for `native_tool_calling`
5. inline Dockerfile patch for default-tools inclusion

Important truth:
- the later inline Dockerfile patch wins over the earlier helper-script default-tools mutation

### sandbox agent-server

Effective winner order before normalization:

1. base image from `ghcr.io/openhands/agent-server:61470a1-python`
2. top-level Python package install for `1.11.4`
3. converter file overrides from `compose/agent_server_override/vendor_sdk/`
4. entrypoint replacement to `python3 -m openhands.agent_server`

### Stagehand MCP

Effective winner:
- `repos/stagehand(working)/packages/mcp/src/server.ts`

There is no competing active Stagehand patch path today.
The problem is not path competition there.
The problem is that the one winning shim is large and only partially documented.

## Patch-authority problems before normalization

1. OpenHands app patch authority is split across:
- vendored file overrides
- one helper patch script
- two inline Dockerfile code mutations

2. The OpenHands helper patch and the inline Dockerfile patch disagree about default-tools behavior.

3. Converter overrides are duplicated across app and sandbox paths.

4. A stale tool-call patch script still exists even though it does not win.

5. Duplicate vendor override files still exist under:
- `compose/agent_server_override/vendor_sdk/vendor_sdk/`

## Safe consolidation targets for this pass

1. Collapse OpenHands app patching into one explicit helper invoked from `compose/openhands_override/Dockerfile`.
2. Move converter overrides to one canonical shared location.
3. Delete the duplicate `vendor_sdk/vendor_sdk/` subtree once the shared location is active.
4. Delete `scripts/patch_openhands_tool_call_mode.py` once the canonical OpenHands patch helper covers the winning behavior.
5. Delete `repos/stagehand(working)/packages/mcp/src/server.ts.bak` once recorded as non-authoritative.

## Patch-authority target after normalization

This pass should leave:

- one OpenHands app patch helper
- one shared converter override location
- one sandbox Dockerfile consuming that shared converter authority
- one Stagehand MCP source file as the browser-lane shim
- no non-winning duplicate patch scripts sitting beside the live path

## Normalization actions applied

Applied in this pass:

1. OpenHands app patch authority was collapsed into:
- `compose/openhands_override/apply_runtime_patches.py`

That helper now owns:
- external-resource prompt bias
- no-repo external-resource suffix
- selected-repository plumbing
- MCP filtering
- skill filtering
- title-callback suppression
- `native_tool_calling` compatibility patch

2. Shared converter authority was collapsed into:
- `compose/shared_vendor_sdk/fn_call_converter.py`
- `compose/shared_vendor_sdk/fn_call_converter_v0.py`

3. Non-winning duplicate patch paths were removed:
- `scripts/patch_openhands_tool_call_mode.py`
- `compose/agent_server_override/vendor_sdk/vendor_sdk/*`
- `compose/agent_server_override/vendor_sdk/*`
- `compose/openhands_override/vendor_sdk/*`
- `repos/stagehand(working)/packages/mcp/src/server.ts.bak`

## Post-normalization patch authority result

### OpenHands app

Active authority now:
- `compose/openhands_override/Dockerfile`
- `compose/openhands_override/apply_runtime_patches.py`
- `compose/shared_vendor_sdk/*`

Important cleanup win:
- the old contradiction between the helper patch and Dockerfile inline default-tools patch is gone
- there is now one OpenHands app patch helper instead of helper-plus-inline mutation drift

### sandbox agent-server

Active authority now:
- `compose/agent_server_override/Dockerfile`
- `compose/shared_vendor_sdk/*`

### Stagehand MCP

Active authority remains:
- `repos/stagehand(working)/packages/mcp/src/server.ts`

No new browser-lane redesign was introduced in this pass.
