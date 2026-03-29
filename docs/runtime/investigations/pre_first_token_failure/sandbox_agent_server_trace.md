# Sandbox Agent-Server Trace

Date context: 2026-03-29

## Sandbox identity

- container name: `oh-agent-server-xC0Bgbvjp2GAUZBX1wvFV`
- container id: `f1c7697604e418298950bb02689d28230ce624fcba5ead65a2713f2bb0d503cc`
- image digest id: `sha256:afdea92ea0044683f4c5c1fa826349a9dad2542c672f8a8f7a37de66e30a2801`
- created: `2026-03-29T16:51:53.483083665Z`

## Entrypoint and startup path

Captured from `docker inspect` during the live repro:

```text
Path: python3
Args:
  - -m
  - openhands.agent_server
  - --port
  - 8000
```

This matches the canonical sandbox image intent in:
- `compose/agent_server_override/Dockerfile`

## Sandbox startup evidence

Live logs captured before smoke cleanup removed the container:

```text
🙌 Starting OpenHands Agent Server on 0.0.0.0:8000
Started server process [7]
Waiting for application startup.
Desktop service is disabled
Tool preload service started successfully
VSCode service started successfully
Server initialization complete - ready to serve requests
Uvicorn running on http://0.0.0.0:8000
GET /health -> 200
GET /alive -> 200
```

This rules out:
- sandbox bootstrap failure
- import failure on `openhands.agent_server`
- agent-server entrypoint failure
- tool preload startup failure

## Exact exception

The failing boundary appears here:

```text
ERROR openhands.agent_server.event_service - Error during conversation run from send_message
...
openai.BadRequestError: Error code: 400 - {'error': {'message': 'Failed to load model "qwen3-coder-30b-a3b-instruct". Error: Failed to load model.', 'type': 'invalid_request_error', 'param': 'model', 'code': None}}
...
litellm.exceptions.BadRequestError: litellm.BadRequestError: OpenAIException - Failed to load model "qwen3-coder-30b-a3b-instruct". Error: Failed to load model.
...
openhands.sdk.llm.exceptions.types.LLMBadRequestError: litellm.BadRequestError: OpenAIException - Failed to load model "qwen3-coder-30b-a3b-instruct". Error: Failed to load model.
...
openhands.sdk.conversation.exceptions.ConversationRunError: Conversation run failed for id=b3e00b80-e57a-4e0d-9be2-b653cb1b2a22: litellm.BadRequestError: OpenAIException - Failed to load model "qwen3-coder-30b-a3b-instruct". Error: Failed to load model.
```

## Classification

The exact sandbox-side failing step is:
- first model dispatch failure

The failing component is:
- LM Studio model loading during the first OpenAI-compatible completion request

What this rules out:
- sandbox startup failure
- OpenHands app ↔ sandbox protocol failure
- config injection failure for model/base/MCP values
- MCP registration failure
- browser tool invocation failure
- event propagation failure

The sandbox does not die before startup.
It dies because the first LLM call returns a hard provider error.
