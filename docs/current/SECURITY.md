# SECURITY

> **Current operational security notes.**
> This is not yet a complete security review, but it reflects the current architecture better than the older Phase A/Ollama-era assumptions.

## Current trust boundaries

- `openhands-app` is trusted infrastructure, not a low-privilege app container.
- `openhands-app` has Docker socket access so it can create per-conversation sandbox containers.
- only the dedicated workspace subtree under `/home/dev/OH_SHOP/workspace` should be exposed as workspace base paths.
- do not mount broad host roots like `/home/dev`.

## Current host/container split

- LM Studio runs on the host and is expected on `127.0.0.1:1234`.
- Dockerized callers reach LM Studio through `http://host.docker.internal:1234/v1`.
- OpenWebUI is a separate operator cockpit, not the OpenHands execution control plane.

## Data and artifact handling

- OpenHands persistence lives under `/home/dev/OH_SHOP/data/openhands`.
- browser/tool artifacts and downloads belong under `/home/dev/OH_SHOP/downloads`.
- OpenWebUI state currently lives in a Docker named volume, so it is off-repo state and must be treated accordingly.

## Practical rules

- keep secrets in environment variables or managed stores, not in repo files
- do not assume a healthy container means a tool is safe or correctly integrated
- treat `chat_guard` as optional/provisional tooling, not a security boundary
