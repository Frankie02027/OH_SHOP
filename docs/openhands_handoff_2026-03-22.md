# OpenHands Handoff Report

Date: 2026-03-22
Workspace: `/home/dev/OH_SHOP`

## Purpose

This report captures the exact state of the OpenHands + `oh-browser-mcp` work at the point progress stopped, so another agent can continue without replaying the same failures.

Primary unfinished proof goals:
- OpenHands API/chat path can autonomously complete: `Get the README file from the openGauss project.`
- OpenHands API/chat path can autonomously complete a harder search/download task for the Czech/Slovak Kodi repo ZIP.
- Proof must come through OpenHands conversation flow, not by calling `oh-browser-mcp` directly.

## Current Top-Level State

What is working:
- `oh-browser-mcp` exists and is wired into compose.
- OpenHands can see MCP tools.
- OpenHands can start conversations through the app API.
- The model attempts tool usage.
- Repo-side manual sandbox cleanup exists.

What is not working:
- The local-model non-native function-calling path is still malformed.
- OpenHands produces broken tool markup instead of a clean executable function call.
- The fresh OpenHands conversation path is therefore not proven end to end for the openGauss/Kodi tasks.
- Automatic post-conversation sandbox teardown is not implemented.

## Exact User-Facing Failure

The live OpenHands UI/API output degraded into malformed pseudo-function markup like:

```text
<function=web_re_search security_risk="LOW">
<parameter=query>https://github.com/opengauss/openGauss</parameter>
<parameter=max_results>10</parameter>
<parameter=max_pages>5</parameter>
<parameter>download>true</parameter>
<parameter>allowed_domains>[</parameter>
<parameter=seed_urls>[ "http://localhost:32983", "http://localhost:35833"]</parameter>
<parameter>security_risk>HIGH</parameter>
<parameter>summary>Search for README file in openGauss repository</parameter>
```

This then triggered OpenHands errors such as:

```text
Function 'web_re_search security_risk="LOW"
<parameter=query' not found in available tools: ['web_research', 'web_re_search', 'finish', 'think']
```

and earlier:

```text
Function 'web_re_search' not found in available tools: ['web_research', 'finish', 'think']
```

The important point is that the failure is in the function-call parsing/execution path, not just in search quality.

## Evidence

Relevant OpenHands conversation artifacts:
- [data/openhands/v1_conversations/51bbbe0d6d404a27b47a070b8904e6ec](/home/dev/OH_SHOP/data/openhands/v1_conversations/51bbbe0d6d404a27b47a070b8904e6ec)
- [data/openhands/v1_conversations/71e3bea9cec247fea20e76d29c83da1c](/home/dev/OH_SHOP/data/openhands/v1_conversations/71e3bea9cec247fea20e76d29c83da1c)
- [data/openhands/v1_conversations/b27e19d003264bbbb1499f6cb1e39382](/home/dev/OH_SHOP/data/openhands/v1_conversations/b27e19d003264bbbb1499f6cb1e39382)
- [data/openhands/v1_conversations/c3fca8b434fe4d7c924422ea2ad29d06](/home/dev/OH_SHOP/data/openhands/v1_conversations/c3fca8b434fe4d7c924422ea2ad29d06)

Most useful individual evidence files:
- [21a3a62d61f546f8a7c7928e2fd999d6.json](/home/dev/OH_SHOP/data/openhands/v1_conversations/51bbbe0d6d404a27b47a070b8904e6ec/21a3a62d61f546f8a7c7928e2fd999d6.json)
- [d4a362447d554e0691a09c786b577be6.json](/home/dev/OH_SHOP/data/openhands/v1_conversations/51bbbe0d6d404a27b47a070b8904e6ec/d4a362447d554e0691a09c786b577be6.json)
- [b0b55b499f99472198bd901a6c27794e.json](/home/dev/OH_SHOP/data/openhands/v1_conversations/71e3bea9cec247fea20e76d29c83da1c/b0b55b499f99472198bd901a6c27794e.json)
- [c1f00002e0a14e7abdb25e01ffb6fbe7.json](/home/dev/OH_SHOP/data/openhands/v1_conversations/b27e19d003264bbbb1499f6cb1e39382/c1f00002e0a14e7abdb25e01ffb6fbe7.json)
- [553dadcd83ab415eb41d508fb5ce3246.json](/home/dev/OH_SHOP/data/openhands/v1_conversations/c3fca8b434fe4d7c924422ea2ad29d06/553dadcd83ab415eb41d508fb5ce3246.json)

Useful grep source:
- `rg -n "Function 'web_re_search|not found in available tools|<function=web_re_search|Get the README file from the openGauss project" data/openhands/v1_conversations`

## What Was Learned

### 1. The wrong OpenHands parser path was patched at first

Early patching focused on:
- [patch_openhands_tool_call_mode.py](/home/dev/OH_SHOP/scripts/patch_openhands_tool_call_mode.py)
- target `/app/openhands/llm/fn_call_converter.py`

But the real non-native tool-calling path for the live LM flow also uses:
- `/app/.venv/lib/python3.13/site-packages/openhands/sdk/llm/mixins/non_native_fc.py`
- `/app/.venv/lib/python3.13/site-packages/openhands/sdk/llm/mixins/fn_call_converter.py`

That SDK converter path became the critical one.

### 2. The model output is malformed in more than one way

Observed issues in the raw generated markup:
- function name contamination:
  - `web_re_search security_risk="LOW"`
- malformed parameter tags:
  - `<parameter>download>true</parameter>`
- bad/partial arrays:
  - `<parameter>allowed_domains>[</parameter>`
- multiple function blocks concatenated together
- stray `<|im_start|>` markers
- injected arguments not in the tool schema:
  - `security_risk`
  - `summary`
- polluted `seed_urls` values containing localhost helper URLs

This means a robust fix likely needs to happen before strict OpenHands tool validation runs, or the model/prompting mode must be changed so it stops emitting this broken syntax.

### 3. Search quality is not the first blocker

Search and browsing still need hardening, but the immediate blocker for the OpenHands proof tasks is function-call parsing/execution.

The openGauss task is currently dying before it gets a fair browse/download attempt.

## Current Temporary Patch Layer

These files are temporary compatibility/hotpatch scaffolding, not a clean final design:
- [patch_openhands_tool_call_mode.py](/home/dev/OH_SHOP/scripts/patch_openhands_tool_call_mode.py)
- [patch_openhands_external_resource_routing.py](/home/dev/OH_SHOP/scripts/patch_openhands_external_resource_routing.py)
- [openhands-entrypoint-wrapper.sh](/home/dev/OH_SHOP/scripts/openhands-entrypoint-wrapper.sh)

What they currently try to do:

### `patch_openhands_tool_call_mode.py`

Goals:
- force `native_tool_calling=False` for `openhands-lm`
- patch both converter targets:
  - `/app/openhands/llm/fn_call_converter.py`
  - `/app/.venv/lib/python3.13/site-packages/openhands/sdk/llm/mixins/fn_call_converter.py`
- loosen regex handling for malformed `<function=...>` blocks
- normalize malformed `<parameter>` tags

Important limitation:
- even after patching both converter paths, live conversations still showed malformed tool-call failures
- so the current patch is not sufficient proof that the real runtime path is fixed

### `patch_openhands_external_resource_routing.py`

Goals:
- bias no-repo conversations toward external internet resources instead of local workspace search
- filter default tools/skills in no-repo mode
- bias prompts toward MCP/browser use

Important limitation:
- this does not solve the broken tool-call syntax problem
- this is also still patch-script scaffolding rather than a real productized configuration path

## Sandbox Cleanup State

Current repo behavior:
- [agent_house.py](/home/dev/OH_SHOP/scripts/agent_house.py) has:
  - `cleanup-sandboxes`
  - `_remove_openhands_sandboxes()`
  - `down` cleanup that removes `oh-agent-server-*`
- [down.sh](/home/dev/OH_SHOP/scripts/down.sh) routes through that cleanup path

What is still missing:
- sandboxes are not being automatically deleted immediately after each finished OpenHands conversation
- they are only cleaned when:
  - `python3 scripts/agent_house.py cleanup-sandboxes`
  - `python3 scripts/agent_house.py down`
  - or other repo scripts explicitly call cleanup

What should be implemented:
- a post-run cleanup hook in the OpenHands API proof harness
- and, if long-running UI use matters, a lifecycle watcher that removes finished/paused `oh-agent-server-*` containers after a grace period

Best-practice direction:
- keep one explicit repo-side cleanup utility for manual recovery
- also add automatic cleanup after proof/API runs complete
- avoid leaving cleanup dependent on the user noticing `docker ps`

## Current `oh-browser-mcp` State

Main relevant files:
- [server.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/server.py)
- [research.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/research.py)
- [searx.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/searx.py)
- [browse.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/browse.py)

Important current observations:
- `server.py` exposes both `web_research` and `web_re_search`
- `server.py` still accepts `seed_urls`
- `searx.py` still contains repo-host-specific ranking/fallback behavior, especially around GitHub/GitLab
- `browse.py` contains generic page/download route hints, pacing, and stealth logic, but earlier drift into site-specific behavior caused user frustration

The current MCP layer is therefore functional but not yet clean:
- some generic browser hardening exists
- some search/ranking logic is still too repo-host-aware
- but again, the top blocker for the requested proof is still the OpenHands tool-call path

## What Must Be Fixed Next

Priority order:

1. Make OpenHands non-native function calling actually execute cleanly
- prove a fresh OpenHands conversation can emit a valid `web_research` or `web_re_search` call
- no malformed `<function=... security_risk="LOW">` strings
- no broken `<parameter>` tags
- no parser error messages in the conversation

2. Re-run the exact user task through OpenHands API
- `Get the README file from the openGauss project.`
- no extra prompt spoonfeeding
- no direct MCP shortcut

3. After that succeeds, run the harder second proof through OpenHands API
- user wanted a search/download task for the Czech/Slovak Kodi repo ZIP
- again through OpenHands conversation flow

4. Only after OpenHands tool calls are clean should search/browse quality be tuned further

## Recommended Continuation Path For Copilot

### A. Stop adding more ad hoc patch scripts

Do not add a third or fourth patch script.

Instead pick one of these two permanent directions:

Option 1:
- vendor the exact OpenHands files being changed into a repo-controlled override layer
- make those source edits explicit and reproducible in the image build

Option 2:
- replace patch-script mutation with a single deterministic build-time overlay for the modified OpenHands files
- no runtime regex surgery at container start

Either option is better than continuing with patch scripts as a permanent design.

### B. Remove the patch scripts correctly

The right cleanup plan is:

1. Identify the exact final upstream files that must differ.
2. Copy those files into a repo-controlled override tree.
3. Change [compose/docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml) or the OpenHands Docker build path so those files are baked into the container image.
4. Delete:
   - [patch_openhands_tool_call_mode.py](/home/dev/OH_SHOP/scripts/patch_openhands_tool_call_mode.py)
   - [patch_openhands_external_resource_routing.py](/home/dev/OH_SHOP/scripts/patch_openhands_external_resource_routing.py)
5. Reduce [openhands-entrypoint-wrapper.sh](/home/dev/OH_SHOP/scripts/openhands-entrypoint-wrapper.sh) to normal startup only, or remove it if no longer needed.

This is the correct path to get rid of the current patch-script layer.

### C. Instrument the failing path before changing prompts again

Before more model or prompt changes:
- inspect the exact runtime code path that handles the malformed markup
- add temporary logging around function-name extraction and parameter normalization in the real converter path
- confirm whether the patched SDK converter is actually the live path used during fresh conversations after restart

The previous session already showed that patching one apparent target was not enough.

### D. Keep proof criteria strict

Proof is not done until:
- OpenHands API conversation succeeds
- tool call actually executes
- answer is non-empty
- `sources >= 2`
- `visited >= 2`
- real download artifact exists in `/home/dev/OH_SHOP/downloads`
- checksum is produced

### E. Finish sandbox lifecycle cleanup properly

Do not stop at `cleanup-sandboxes` as a manual command.

Implement:
- automatic cleanup after each scripted OpenHands API proof run
- automatic cleanup on failed proof runs too
- optional watcher/TTL cleanup for stale paused `oh-agent-server-*` containers created from UI chats

This should eliminate the current pattern where sandboxes accumulate until someone runs manual cleanup.

## Suggested Copilot Starting Checklist

1. Read this report.
2. Inspect:
   - [patch_openhands_tool_call_mode.py](/home/dev/OH_SHOP/scripts/patch_openhands_tool_call_mode.py)
   - [patch_openhands_external_resource_routing.py](/home/dev/OH_SHOP/scripts/patch_openhands_external_resource_routing.py)
   - [browse.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/browse.py)
   - [searx.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/searx.py)
3. Inspect the real OpenHands runtime converter path inside the container.
4. Replace runtime patching with a proper override/build strategy.
5. Re-run the exact openGauss task through the OpenHands API.
6. Only after that passes, run the Kodi ZIP task.

## Short Blunt Summary

The main unfinished problem is not “how to search GitHub better.”

The main unfinished problem is:
- OpenHands plus the local model is still emitting malformed function-call markup
- OpenHands is therefore failing before it can reliably perform the requested browse/download tasks

The patch scripts were a debugging bridge, not a proper final architecture, and they should be replaced by a clean build-time override approach.
