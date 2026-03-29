# Phase A Implementation Log and Verification Proof

> **Historical / non-authoritative document.**
> This file is a Phase A execution log from the earlier Ollama-era setup.
> It is retained as implementation history, not as current setup guidance.
> For the active operational baseline, use [SETUP.md](/home/dev/OH_SHOP/docs/SETUP.md).

Date: 2026-03-05 (America/Chicago)  
Workspace root: `/home/dev/OH_SHOP`  
Author: Codex (execution transcript condensed with command/output proofs)

---

## 1) Objective

Implement `docs/SETUP.md` Phase A stack:

- OpenHands GUI on `:3000`
- OpenWebUI on `:3001`
- Ollama API on `:11434`
- SearxNG JSON API on `:3002`
- Docker Engine standardization (replace Podman Docker shim)
- Host/container networking for OpenHands sandboxes -> Ollama (`host.docker.internal`)

---

## 2) What Was Done (Detailed)

### 2.1 Created required folders

Created exactly as requested:

- `/home/dev/OH_SHOP/{compose,data,repos,downloads}`
- `/home/dev/OH_SHOP/data/{ollama,openwebui,searxng,openhands}`

### 2.2 Updated compose stack to match SETUP contract

Replaced the existing compose file with required services:

- `open-webui` (`ghcr.io/open-webui/open-webui:main`) on `3001:8080`
- `searxng` (`searxng/searxng:latest`) on `3002:8080`
- `open-webui` configured with `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- `extra_hosts: host.docker.internal:host-gateway`
- named volumes for OpenWebUI and SearxNG

File changed:

- `/home/dev/OH_SHOP/compose/docker-compose.yml`

### 2.3 Migrated from Podman Docker shim to Docker Engine

Performed root-required setup:

1. Removed `podman-docker`.
2. Added Docker apt keyring/repo.
3. Installed:
   - `docker-ce`
   - `docker-ce-cli`
   - `containerd.io`
   - `docker-buildx-plugin`
   - `docker-compose-plugin`
4. Enabled/started docker service.
5. Added user `dev` to `docker` group.

Environment-specific fixes made during install:

- `VERSION_CODENAME=echo` (Parrot) has no Docker repo -> switched to Debian `trixie` repo path.
- Existing `docker-compose` package conflicted with Docker compose plugin binary path -> removed legacy `docker-compose`, then installed `docker-compose-plugin`.

### 2.4 Brought up OpenWebUI + SearxNG with Docker Engine

Started services from:

- `/home/dev/OH_SHOP/compose`

using Docker socket:

- `DOCKER_HOST=unix:///var/run/docker.sock docker compose up -d`

### 2.5 Enabled SearxNG JSON output (required)

Inside SearxNG settings:

- ensured:
  - `search.formats` includes `json` and `html`

Then restarted `searxng`.

### 2.6 Fixed Ollama host binding for container access

Observed Ollama listening only on loopback (`127.0.0.1:11434`) which prevents container access via host gateway.

Implemented systemd override:

- file: `/etc/systemd/system/ollama.service.d/override.conf`
- value:
  - `Environment="OLLAMA_HOST=0.0.0.0:11434"`

Reloaded systemd and restarted Ollama.

### 2.7 Fixed host firewall path from Docker bridge to Ollama

Observed `host.docker.internal:11434` timeout from containers due UFW default deny.

Added rule:

- `ufw allow in on docker0 to any port 11434 proto tcp`

This restored container->host Ollama connectivity.

### 2.8 OpenHands runtime preparation and startup validation

1. Pulled OpenHands runtime image (`docker.openhands.dev/openhands/runtime:latest-nikolaik`).
2. Pulled OpenHands app image (`docker.openhands.dev/openhands/openhands:latest`).
3. Verified OpenHands GUI responds on `http://localhost:3000`.

Important behavior discovered:

- `openhands serve` in this CLI version invokes `docker run -it` and requires a TTY.
- Non-interactive/background launches fail with:
  - `the input device is not a TTY`

### 2.9 Persistence path pinning

SETUP requested OpenHands persistence under OH_SHOP data.

OpenHands CLI mounted `~/.openhands` directly, so to enforce the target path:

- linked `/home/dev/.openhands -> /home/dev/OH_SHOP/data/openhands`

### 2.10 Persisted env defaults for future shells

Added to shell startup files:

- `/home/dev/.bashrc`
- `/home/dev/.profile`

Exports:

- `DOCKER_HOST=unix:///var/run/docker.sock`
- `OH_PERSISTENCE_DIR=/home/dev/OH_SHOP/data/openhands`

---

## 3) Verification Proof (Command/Output)

### 3.1 Timestamp + required directories

```text
=== timestamp ===
2026-03-05T06:34:36-06:00

=== workspace dirs ===
drwxrwxr-x 1 dev dev 136 Mar  5 06:04 /home/dev/OH_SHOP
drwxrwxr-x 1 dev dev  36 Mar  5 05:33 /home/dev/OH_SHOP/compose
drwxrwxr-x 1 dev dev  62 Mar  5 06:04 /home/dev/OH_SHOP/data
drwxrwxr-x 1 dev dev   0 Mar  5 06:04 /home/dev/OH_SHOP/downloads
drwxrwxr-x 1 dev dev   0 Mar  5 06:04 /home/dev/OH_SHOP/repos
drwxrwxr-x 1 dev dev  0 Mar  5 06:04 /home/dev/OH_SHOP/data/ollama
drwxrwxr-x 1 dev dev 22 Mar  5 06:25 /home/dev/OH_SHOP/data/openhands
drwxrwxr-x 1 dev dev  0 Mar  5 06:04 /home/dev/OH_SHOP/data/openwebui
drwxrwxr-x 1 dev dev  0 Mar  5 06:04 /home/dev/OH_SHOP/data/searxng
```

### 3.2 Docker Engine and compose plugin installed + running

```text
=== docker versions ===
Docker version 29.2.1, build a5c7197
Docker Compose version v5.1.0

=== docker service ===
active
enabled

=== docker packages ===
ii containerd.io                2.2.1-1~debian.13~trixie
ii docker-buildx-plugin         0.31.1-1~debian.13~trixie
ii docker-ce                    5:29.2.1-1~debian.13~trixie
ii docker-ce-cli                5:29.2.1-1~debian.13~trixie
ii docker-ce-rootless-extras    5:29.2.1-1~debian.13~trixie
ii docker-compose-plugin        5.1.0-1~debian.13~trixie
```

### 3.3 Service containers up

```text
=== running containers ===
NAMES        IMAGE                                STATUS                    PORTS
open-webui   ghcr.io/open-webui/open-webui:main   Up 17 minutes (healthy)   0.0.0.0:3001->8080/tcp
searxng      searxng/searxng:latest               Up 16 minutes             0.0.0.0:3002->8080/tcp
```

### 3.4 Endpoint proofs

```text
HTTP/1.1 200 OK   (http://localhost:3001)

{"query":"test", ... }   (http://localhost:3002/search?q=test&format=json)

{"models":[{"name":"glm-4.7-flash:latest", ... }]}   (http://localhost:11434/api/tags)
```

### 3.5 SearxNG JSON format proof

```text
formats:
  - json
  - html
```

### 3.6 Ollama bind + firewall + container reachability proof

```text
=== ollama bind + override ===
LISTEN ... *:11434 ...
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"

=== firewall rule ===
[ 2] 11434/tcp on docker0       ALLOW IN    Anywhere

=== host.docker.internal from docker ===
{"models":[{"name":"glm-4.7-flash:latest", ... }]}
```

### 3.7 OpenHands proof

OpenHands startup validation was executed under pseudo-TTY (required by current CLI).

```text
poll-1:000
...
poll-7:200
HTTP/1.1 200 OK
```

Runtime/container proof:

```text
NAMES           STATUS          PORTS
openhands-app   Up 27 seconds   0.0.0.0:3000->3000/tcp
...
Uvicorn running on http://0.0.0.0:3000
GET / ... 200 OK
HEAD / ... 200 OK
```

---

## 4) Phase A Acceptance Mapping

### A1) OpenHands UI loads (`http://localhost:3000`)

- Status: **PASS**
- Proof: `HTTP/1.1 200 OK` during OpenHands serve session.

### A2) OpenWebUI loads (`http://localhost:3001`)

- Status: **PASS**
- Proof: `HTTP/1.1 200 OK`.

### A3) Ollama alive (host)

- Status: **PASS**
- Proof: `/api/tags` returns model JSON.

### A4) SearxNG JSON works

- Status: **PASS**
- Proof: `/search?...&format=json` returns JSON payload.

### A5) OpenHands can create file in `/workspace`

- Status: **PENDING manual UI interaction**
- Not executed from terminal-only automation in this run.

### A6) OpenHands sandbox terminal command (`ls -la /workspace`)

- Status: **PENDING manual UI interaction**

### A7) OpenHands can talk to Ollama

- Status: **PENDING manual UI interaction**
- Infrastructure dependency is validated (container->host Ollama connectivity now works).

---

## 5) Files/Configs Changed

- `/home/dev/OH_SHOP/compose/docker-compose.yml`
- `/etc/apt/sources.list.d/docker.list`
- `/etc/apt/keyrings/docker.gpg`
- `/etc/systemd/system/ollama.service.d/override.conf`
- `/home/dev/.bashrc`
- `/home/dev/.profile`
- `/home/dev/.openhands` (symlink to `/home/dev/OH_SHOP/data/openhands`)

---

## 6) Current Runtime State (at doc creation)

- `open-webui` running on `3001`
- `searxng` running on `3002`
- `openhands-app` currently running on `3000` (launched during proof capture)
- Ollama service active and listening on `0.0.0.0:11434`
