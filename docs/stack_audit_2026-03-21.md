# Stack Audit - 2026-03-21

## Why this document exists

This report is the authoritative description of what the OH_SHOP stack is actually doing today.

It exists because the project accumulated multiple partially-true stories:

- original setup docs
- phase docs
- compose files
- live runtime behavior
- later recovery patches

Those stories no longer matched each other cleanly.

This audit answers four questions:

1. What is running on the host OS right now?
2. What is running in Docker right now?
3. Which parts of the project are implemented versus merely planned?
4. What is the most sane and professional way to define the stack going forward?

## High-level conclusion

The core problem was not "OpenHands in Docker" by itself.

The core problem was architectural drift:

- the docs largely described one stack
- the live runtime was already using a somewhat different stack
- the local model provider changed from Ollama to LM Studio
- the custom Phase B tooling was implemented, but not fully wired into OpenHands settings

So the stack became a mix of:

- old assumptions
- new runtime behavior
- partial integration work
- stale state carried forward from earlier configurations

That is why the environment started feeling haunted.

## Executive summary

If someone unfamiliar with the repo needs the shortest accurate read, it is this:

- the host OS should own machine-level responsibilities such as Docker Engine and LM Studio
- the long-running application services should live in Docker
- the actual OpenHands execution work should happen in separate Docker sandbox containers
- the project drifted because docs, runtime, and provider choices stopped describing the same stack
- the cleanup should converge the repo on one truthful story rather than preserve every historical path

In other words:

- containerization is not the problem
- inconsistent architecture narratives are the problem

## Key judgment in plain English

### What is normal

These things are normal and professionally sane:

- host OS runs Docker daemon
- host OS runs a local model server like LM Studio
- application services run in containers
- execution sandboxes run in separate containers
- web/search/helper services run in containers
- persistent state lives in explicit mounted directories

### What is not normal

These things are not sane long-term:

- docs describe a host-launched lane as if it were the active truth
- runtime uses a Docker-backed controller path instead
- docs still describe Ollama as canonical while live stack uses LM Studio
- custom MCP tooling exists but is not actually registered in OpenHands settings
- old state and new architecture are mixed together without a reset

## Evidence used

This audit is based on:

- live process inspection
- live listening ports
- live Docker containers and Docker networks
- live OpenHands settings and persistence files
- local phase/setup docs
- local compose files
- local OpenHands CLI behavior on this machine

Primary repo files:

- `docs/SETUP.md`
- `docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md`
- `docs/phase_1_consolidated_oh_shop.md`
- `docs/Phase_A.md`
- `docs/phase_2_review_pack_artifacts.md`
- `compose/docker-compose.yml`
- `compose/openhands.compose.yml`
- `repos/oh-browser-mcp/README.md`
- `artifacts/ollama_model_inventory_2026-03-06.txt`

Runtime facts checked directly:

- `ps`
- `ss -lntp`
- `docker ps`
- `docker inspect`
- OpenHands API settings
- installed OpenHands CLI help and source behavior

## What this audit is not claiming

This document is not claiming that:

- the current stack is fully broken
- Docker-backed OpenHands is inherently wrong
- LM Studio is the wrong choice in all cases
- historical docs were unreasonable when written

This document is claiming that:

- the project no longer had one canonical description
- that ambiguity directly caused wasted debugging effort
- the stack must now be defined by current live truth, not remembered intent alone

## Current live architecture

## Host OS responsibilities today

The host OS is currently responsible for:

- running Docker Engine (`dockerd`)
- running LM Studio
- exposing LM Studio API on localhost
- holding the persistent OH_SHOP data directories
- holding the OH_SHOP repo and downloaded artifacts
- running the LM Studio Docker DNAT helper service

Host-side tools currently installed:

- `docker`
- `lmstudio`
- `lms`
- `openhands` CLI 1.13.0

Important nuance:

- the installed `openhands serve` path on this machine launches the OpenHands GUI server using Docker
- therefore, the currently installed OpenHands CLI does not provide a clean "pure host-native controller" path as its default supported local mode

## Container responsibilities today

Long-running containers:

- `openhands-app`
- `open-webui`
- `searxng`
- `oh-browser-mcp`
- `openhands-chat-guard`

Per-conversation containers:

- `oh-agent-server-*`

Those per-conversation containers are the actual execution sandboxes used by OpenHands sessions.

## Current control plane vs execution plane

### Control plane

Current control plane consists of:

- LM Studio on host
- Docker daemon on host
- OpenHands controller in Docker
- OpenWebUI in Docker

### Execution plane

Current execution plane consists of:

- per-conversation `oh-agent-server-*` containers
- tool execution inside those containers
- workspace operations performed inside those containers

This means the actual editing/execution path is still containerized, which is the right safety direction.

## Current network layout

### Host loopback ports

- `127.0.0.1:3000` -> `openhands-app`
- `127.0.0.1:3001` -> `open-webui`
- `127.0.0.1:3002` -> `searxng`
- `127.0.0.1:3010` -> `oh-browser-mcp`
- `127.0.0.1:1234` -> LM Studio API

### Host bridge exposure

- `172.17.0.1:3000` -> `openhands-app`

That bridge exposure was added so agent containers on Docker's default bridge network could reach the OpenHands default MCP endpoint.

### Docker networks

`compose_default` contains:

- `openhands-app`
- `open-webui`
- `searxng`
- `oh-browser-mcp`
- `openhands-chat-guard`

`bridge` contains:

- spawned `oh-agent-server-*` containers

This split matters, because the controller container and the execution containers are not on the same Docker network by default.

That was one of the direct causes of the disappearing-message bug.

## Current storage layout

### Persistent OpenHands data

- `/home/dev/OH_SHOP/data/openhands`

Important files:

- `settings.json`
- `openhands.db`
- `.jwt_secret`
- `.keys`

Legacy path:

- `/home/dev/.openhands` -> symlink to `/home/dev/OH_SHOP/data/openhands`

### Repo exposure

The controller container sees:

- `/home/dev/OH_SHOP/repos` mounted as `/opt/workspace_base`

The spawned runtime containers then create per-conversation workspaces.

This is better than mounting all of `/home/dev`, but it still means the architecture is privileged and must be documented precisely.

### Browser MCP data

- `/home/dev/OH_SHOP/data/oh_browser_mcp`
- `/home/dev/OH_SHOP/downloads`

## Current known-good baseline

As of this audit, the following statements describe the best current operational baseline:

- LM Studio is running on the host
- LM Studio API is expected at `127.0.0.1:1234` on the host
- container callers should reach LM Studio through `http://host.docker.internal:1234/v1`
- OpenHands is running as `openhands-app` in Docker
- OpenHands execution happens in per-conversation `oh-agent-server-*` containers
- OpenWebUI, SearxNG, `oh-browser-mcp`, and `openhands-chat-guard` are long-running Docker services
- OpenHands persistence is under `/home/dev/OH_SHOP/data/openhands`
- current OpenHands settings use a provider-qualified model string

This baseline is not the same thing as "everything is perfect."
It is simply the most accurate description of the stack that exists today.

## Decision matrix by component

### OpenHands controller

- current placement: Docker
- recommended status: keep as canonical
- reason: matches installed CLI behavior, compose reality, and current runtime

### OpenHands execution sandboxes

- current placement: Docker
- recommended status: keep as canonical
- reason: this is the correct containment model for agent execution

### LM Studio

- current placement: host
- recommended status: keep as canonical
- reason: local model service on the host is a normal pattern and simplifies GPU/model ownership

### OpenWebUI

- current placement: Docker
- recommended status: keep as canonical
- reason: it is a service layer and benefits from container isolation

### SearxNG

- current placement: Docker
- recommended status: keep as canonical
- reason: this is exactly the kind of supporting service that fits well in a container

### `oh-browser-mcp`

- current placement: Docker
- recommended status: keep as canonical, but wire it into OpenHands
- reason: it is already the most concrete implemented browsing path in the repo

### `openhands-chat-guard`

- current placement: Docker
- recommended status: keep for now, but treat as optional operational glue rather than architecture-defining
- reason: it is not the cause of the major runtime drift, but it is also not core to the architecture story

### Ollama

- current placement: not the active live lane
- recommended status: demote to historical or fallback only
- reason: keeping it described as canonical would preserve provider ambiguity

## What each major component is doing

## OpenHands

### What it is doing now

- OpenHands controller is running in the `openhands-app` container
- OpenHands spawns per-conversation `oh-agent-server-*` containers
- those agent-server containers handle actual session tools, terminal, file editor, browser tool set, etc.

### What was misunderstood earlier

Some project docs read as if OpenHands was more host-native than it really is.

But on this machine:

- the installed CLI's `serve` path is already Docker-backed
- the compose stack is also Docker-backed

So the more honest statement is:

- OpenHands is currently and practically a Docker-backed controller plus Docker execution sandboxes

## OpenWebUI

### What it is doing now

- OpenWebUI is running in Docker
- it acts as a cockpit/chat UI
- it is not yet bridged into OpenHands automation

### Is that sane?

Yes.

For this project, keeping OpenWebUI in Docker is a professional and reasonable choice.
It is a service/UI layer, not the component that should directly touch the host filesystem for code execution.

## LM Studio

### What it is doing now

- LM Studio runs on the host
- it exposes an OpenAI-compatible API on `127.0.0.1:1234`
- Docker traffic is forwarded to it through the DNAT helper

### Is that sane?

Yes.

This is a very normal local-model pattern:

- model server on host
- containers call it through a controlled host route

## LiteLLM

### What it is

LiteLLM is not part of LM Studio.

It is the provider abstraction layer inside OpenHands that helps OpenHands speak to different model providers through one interface.

The request path is conceptually:

- OpenHands
- LiteLLM
- LM Studio
- loaded local model

### Why it mattered here

Because LiteLLM expects provider-qualified model naming in this path.

That is why:

- bare model name failed
- provider-qualified model name worked

This was not LM Studio being broken.
It was a compatibility rule in the layer between OpenHands and LM Studio.

## SearxNG and custom browsing tools

### What exists right now

- SearxNG is running and healthy
- `oh-browser-mcp` is running and healthy
- `oh-browser-mcp` implements the real Phase B browsing direction better than the old placeholder docs

### What is missing

OpenHands saved MCP config is empty.

That means:

- the custom browsing/search tool exists
- but OpenHands is not currently configured to use it

This is a major implemented-vs-wired mismatch.

## What the project docs originally intended

The original project mission was not just "make OpenHands answer prompts."

It was a local-first agent house:

- OpenHands as executor
- OpenWebUI as cockpit
- local LLM provider
- custom search/internet via self-hosted tools
- later bridge between OpenWebUI and OpenHands

That intent is still valid.

The problem is not the mission.
The problem is that the implementation drifted away from a single documented truth.

## Timeline of drift

## 2026-03-05

The contract and setup docs were created around this picture:

- OpenHands launched through `openhands serve`
- Docker sandboxes for execution
- Ollama as canonical provider

But the compose-based OpenHands lane also already existed on the same day.

This strongly suggests that two setup lanes existed almost from the beginning:

- documented lane
- compose/container lane

## 2026-03-06

The model layer drift became explicit:

- docs still centered on Ollama
- model inventory artifact already shows LM Studio models pulled

This is the first hard proof that the project's "brain" changed without the full stack docs being normalized.

## 2026-03-21

Recovery work exposed the underlying drift:

- agent containers could not reach the controller MCP endpoint
- bare LM Studio model name broke LiteLLM provider resolution
- fresh conversations and old persisted state were carrying different assumptions

## Root causes

## Root cause 1: multiple controller stories

The project simultaneously carried:

- docs implying one launch/control model
- compose files using another
- installed CLI behavior supporting a Docker-backed controller path

This made controller placement and controller reachability unclear.

## Root cause 2: model-provider drift

The project simultaneously carried:

- Ollama-centric docs
- LM Studio live runtime

That changed:

- startup assumptions
- networking assumptions
- model naming assumptions
- troubleshooting assumptions

## Root cause 3: implemented-but-not-wired components

Some pieces were built but not actually integrated into the live user settings.

Most important example:

- `oh-browser-mcp` exists and works
- OpenHands is not currently configured to use it

## Root cause 4: stale state

Old conversations and saved settings preserved assumptions from earlier configurations.

That means even after infrastructure fixes, some sessions can still behave like they belong to an older version of the stack.

## Current unresolved issues

These are the main gaps still separating the stack from "coherent and boring":

### Issue 1: browsing tools exist but are not fully attached

- `oh-browser-mcp` is healthy
- OpenHands saved MCP configuration is empty
- therefore the agent cannot be assumed to have the browsing path that Phase B intended

### Issue 2: model/tool-calling compatibility remains a separate question

Infrastructure recovery and provider-name fixes do not automatically guarantee perfect tool use.

Even when the stack is reachable, the local model path still has to emit tool-calling behavior in a format OpenHands actually consumes.

This means there are two distinct layers of success:

- the transport/config layer works
- the model behavior layer works

Those should not be conflated.

### Issue 3: stale docs still exist outside these new audit artifacts

Until the setup and phase docs are rewritten, a new reader can still walk into an older mental model and recreate the confusion.

## What "normal" should mean after cleanup

After cleanup, a technically literate teammate should be able to answer these questions quickly and consistently:

1. Where does the model run?
   - on the host in LM Studio
2. Where does OpenHands run?
   - in Docker as the controller service
3. Where does actual agent execution happen?
   - in separate Docker sandbox containers
4. Where does OpenWebUI run?
   - in Docker
5. Which provider story is current?
   - LM Studio, not Ollama
6. Which browsing path is current?
   - `oh-browser-mcp`, once registered into OpenHands

If a future doc or script gives different answers, that should be treated as drift immediately.

## Final recommendation

The most sane and professional interpretation of this project is:

- host owns machine concerns
- Docker owns app services
- separate Docker sandboxes own agent execution
- docs must describe that exact split
- old provider/controller stories must be demoted instead of kept half-alive

That recommendation is intentionally conservative.
It does not chase novelty.
It simply aligns the repo with the stack that is actually present and supportable on this machine.

## Professional sanity check

## If this were a professional environment, what would be considered sane?

A professional team could absolutely run a stack shaped like this:

- host OS runs Docker daemon and local model server
- application services run in containers
- worker/sandbox execution runs in separate containers
- custom tool servers are separate services
- persistence is mounted to explicit directories

That is not weird.
That is actually a very common pattern.

## What professionals would not tolerate

Professionals generally would not accept:

- setup docs that describe a different architecture than production
- active runtime using a different LLM provider than the docs
- custom tool service built but not actually attached
- multiple "maybe canonical" startup paths
- no clear statement of host-vs-container responsibility

So the professional answer is:

- the intended architecture is fine
- the undocumented drift is what made it brittle

## Recommended canonical architecture

This audit recommends the following as the single authoritative baseline going forward:

### Host OS

- Docker Engine
- LM Studio
- LM Studio localhost API
- LM Studio Docker DNAT helper
- OH_SHOP source/data/artifacts

### Docker application services

- OpenHands controller (`openhands-app`)
- OpenWebUI
- SearxNG
- `oh-browser-mcp`
- chat guard

### Docker execution services

- per-conversation `oh-agent-server-*` containers

### What this means in plain language

- model runs on host
- applications run in Docker
- actual agent work runs in separate Docker sandboxes

That is a sane and professional architecture for this project.

## What should be considered non-authoritative after this audit

These should no longer be treated as active truth unless intentionally restored:

- Ollama as the current canonical provider
- any doc language implying a pure host-native OpenHands controller as the active live stack
- Phase B placeholder MCP docs that ignore the implemented `oh-browser-mcp` path

## Biggest current mismatches still remaining

1. Docs still contain competing controller/provider stories.
2. `oh-browser-mcp` is implemented but not registered in OpenHands settings.
3. Old OpenHands state still exists and may preserve stale assumptions.
4. Some auxiliary errors remain noisy, especially around title generation and fresh-conversation edge cases.

## Recommended next steps after this audit

1. Normalize docs around the Docker-backed controller + LM Studio baseline.
2. Normalize startup scripts and verification around the same baseline.
3. Register `oh-browser-mcp` in OpenHands MCP settings.
4. Back up and reset stale OpenHands state.
5. Re-verify on a fresh conversation only.

## Final judgment

The right move is not to keep layering ad hoc patches forever.

The right move is:

- choose one architecture
- make docs match it
- make scripts match it
- make settings match it
- reset stale state after backup

Once that is done, the project becomes much less mysterious.

The containerization itself is not the weird part.
The competing truths were the weird part.
