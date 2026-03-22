#!/usr/bin/env python3
"""Agent House orchestration entrypoint for the canonical compose baseline."""

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "compose" / "docker-compose.yml"
PROOF_TEMPLATE = ROOT / "docs" / "templates" / "fresh_session_mcp_proof_run.md"
OPENHANDS_SETTINGS_FILE = ROOT / "data" / "openhands" / "settings.json"
OPENHANDS_URL = "http://localhost:3000"
CORE_SERVICES = ["openhands", "open-webui", "searxng", "oh-browser-mcp"]
CORE_CONTAINERS = {
    "OpenHands": "openhands-app",
    "OpenWebUI": "open-webui",
    "SearxNG": "searxng",
    "oh-browser-mcp": "oh-browser-mcp",
}
OPENHANDS_SANDBOX_NAME_PREFIX = "oh-agent-server-"
EXPECTED_MCP_URL = "http://host.docker.internal:3010/sse"
OPENHANDS_TOOL_CALL_PATCH_TARGET = (
    "/app/openhands/app_server/app_conversation/"
    "live_status_app_conversation_service.py"
)
DEFAULT_WEB_RESEARCH_PROOF_PROMPT = (
    "Use the web_research tool to find the current temperature in "
    "Burbank, IL. Cite the source you used and say explicitly that "
    "you used web_research."
)


def get_docker_bridge_gateway() -> str:
    try:
        output = subprocess.check_output(
            [
                "docker",
                "network",
                "inspect",
                "bridge",
                "--format",
                "{{(index .IPAM.Config 0).Gateway}}",
            ],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        output = ""

    return output or os.getenv("DOCKER_BRIDGE_GATEWAY", "172.17.0.1")


def run_compose(args: list[str]) -> int:
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE), *args]
    env = os.environ.copy()
    env.setdefault("DOCKER_BRIDGE_GATEWAY", get_docker_bridge_gateway())
    return subprocess.call(cmd, env=env)


def _list_openhands_sandboxes() -> list[str]:
    ok, output = _run_capture(
        [
            "docker",
            "ps",
            "-aq",
            "--filter",
            f"name={OPENHANDS_SANDBOX_NAME_PREFIX}",
        ],
        timeout=10,
    )
    if not ok or not output.strip():
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _remove_openhands_sandboxes() -> tuple[bool, str]:
    sandbox_ids = _list_openhands_sandboxes()
    if not sandbox_ids:
        return True, "no OpenHands sandbox containers found"

    ok, output = _run_capture(
        ["docker", "rm", "-f", *sandbox_ids],
        timeout=60,
    )
    if not ok:
        return False, output or "failed to remove sandbox containers"
    return True, f"removed {len(sandbox_ids)} OpenHands sandbox container(s)"


def cmd_up() -> int:
    agent_server_rc = subprocess.call(
        [
            "docker",
            "build",
            "-t",
            "oh-shop/agent-server:61470a1-python-patched",
            str(ROOT / "compose" / "agent_server_override"),
        ]
    )
    if agent_server_rc != 0:
        return agent_server_rc
    return run_compose(["up", "-d", "--build", *CORE_SERVICES])


def cmd_down() -> int:
    compose_rc = run_compose(["down"])
    sandboxes_ok, sandboxes_detail = _remove_openhands_sandboxes()
    status = "PASS" if sandboxes_ok else "FAIL"
    print(f"[{status}] OpenHands sandbox cleanup - {sandboxes_detail}")
    return compose_rc if compose_rc != 0 else (0 if sandboxes_ok else 1)


def cmd_logs() -> int:
    return run_compose(["logs", "-f", "--tail", "100"])


def cmd_reconcile_chats() -> int:
    script = ROOT / "scripts" / "chat_guard.py"
    return subprocess.call(["python3", str(script)])


def cmd_monitor_chats() -> int:
    script = ROOT / "scripts" / "chat_guard.py"
    interval = os.getenv("CHAT_GUARD_INTERVAL", "60")
    return subprocess.call(
        ["python3", str(script), "--watch", "--interval", interval]
    )


def _write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run_capture(
    cmd: list[str],
    timeout: int | None = None,
) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)

    output = (completed.stdout or completed.stderr or "").strip()
    return completed.returncode == 0, output


def _request_json_any(
    url: str,
    timeout: int = 5,
    method: str = "GET",
    payload: Any | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[bool, Any, str]:
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")

    request = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            body = ""
        message = f"HTTP {exc.code}"
        if body:
            message = f"{message}: {body}"
        return False, None, message
    except Exception as exc:
        return False, None, str(exc)

    if not raw_body.strip():
        return True, None, ""

    try:
        decoded = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        return False, None, f"invalid JSON response: {exc}"
    return True, decoded, ""


def _fetch_json(url: str, timeout: int = 5) -> tuple[bool, dict | None, str]:
    ok, payload, detail = _request_json_any(url, timeout=timeout)
    if not ok:
        return False, None, detail
    if not isinstance(payload, dict):
        payload_type = type(payload).__name__
        return False, None, "unexpected JSON payload type: " + payload_type
    return True, payload, ""


def _fetch_conversation_events(
    app_conversation_id: str,
    conversation_api_url: str,
    sandbox_headers: dict[str, str],
    timeout: int = 15,
) -> tuple[bool, dict[str, Any] | None, str]:
    """Prefer the app-server v1 event feed; fall back to sandbox."""

    attempts: list[tuple[str, str, dict[str, str] | None]] = [
        (
            "app-server",
            (
                f"{OPENHANDS_URL}/api/v1/conversation/"
                f"{urllib.parse.quote(app_conversation_id)}/events/search"
                "?sort_order=TIMESTAMP&limit=100"
            ),
            None,
        ),
        (
            "sandbox",
            (
                f"{conversation_api_url}/events/search"
                "?sort_order=TIMESTAMP&limit=100"
            ),
            sandbox_headers,
        ),
    ]

    failures: list[str] = []
    sparse_app_payload: dict[str, Any] | None = None
    for source, url, headers in attempts:
        ok, payload, detail = _request_json_any(
            url,
            headers=headers,
            timeout=timeout,
        )
        if ok and isinstance(payload, dict):
            items = payload.get("items")
            if (
                source == "app-server"
                and (
                    not isinstance(items, list)
                    or not items
                    or not _has_runtime_events(items)
                )
            ):
                sparse_app_payload = payload
                failures.append(f"{source}: no runtime events yet")
                continue
            return True, payload, source
        failure_detail = (
            detail
            or (
                f"unexpected payload type: {type(payload).__name__}"
                if payload is not None
                else "empty response"
            )
        )
        failures.append(f"{source}: {failure_detail}")

    if sparse_app_payload is not None:
        return True, sparse_app_payload, "app-server-sparse"

    return False, None, "; ".join(failures)


def _load_json_file(path: Path) -> tuple[bool, dict | None, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, None, f"file not found: {path}"
    except Exception as exc:
        return False, None, str(exc)

    if not isinstance(payload, dict):
        payload_type = type(payload).__name__
        return False, None, f"unexpected JSON payload type: {payload_type}"
    return True, payload, ""


def _content_text(content: Any) -> str:
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return "\n".join(parts).strip()


def _has_runtime_events(items: Any) -> bool:
    if not isinstance(items, list):
        return False

    for event in items:
        if not isinstance(event, dict):
            continue
        kind = event.get("kind")
        if kind in {"ActionEvent", "ObservationEvent"}:
            return True
        if kind == "MessageEvent" and event.get("source") == "agent":
            return True
    return False


def _extract_web_research_events(
    items: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str, str]:
    if not isinstance(items, list):
        return None, None, "", ""

    def _is_web_research_tool_name(name: object) -> bool:
        if not isinstance(name, str):
            return False
        return name in {"web_research", "web_re_search"} or name.endswith(
            "_web_research"
        )

    tool_action = next(
        (
            event
            for event in items
            if (
                isinstance(event, dict)
                and event.get("kind") == "ActionEvent"
                and _is_web_research_tool_name(event.get("tool_name"))
            )
        ),
        None,
    )

    tool_call_id = None
    if isinstance(tool_action, dict):
        tool_call_id = tool_action.get("tool_call_id")

    observation_event = next(
        (
            event
            for event in items
            if (
                isinstance(event, dict)
                and event.get("kind") == "ObservationEvent"
                and event.get("tool_call_id") == tool_call_id
            )
        ),
        None,
    )

    assistant_text = ""
    for event in reversed(items):
        if not isinstance(event, dict):
            continue
        if (
            event.get("kind") == "MessageEvent"
            and event.get("source") == "agent"
        ):
            assistant_text = _content_text(
                event.get("llm_message", {}).get("content")
            )
            if assistant_text:
                break
        if (
            event.get("kind") == "ActionEvent"
            and event.get("tool_name") == "finish"
        ):
            message = event.get("action", {}).get("message")
            if isinstance(message, str) and message.strip():
                assistant_text = message.strip()
                break
        if (
            event.get("kind") == "ObservationEvent"
            and event.get("tool_name") == "finish"
        ):
            assistant_text = _content_text(
                event.get("observation", {}).get("content")
            )
            if assistant_text:
                break

    observation_text = ""
    if isinstance(observation_event, dict):
        observation_text = _content_text(
            observation_event.get("observation", {}).get("content")
        )

    return tool_action, observation_event, assistant_text, observation_text


def _split_provider_model(model: object) -> tuple[str | None, str | None]:
    if not isinstance(model, str) or "/" not in model:
        return None, model if isinstance(model, str) else None
    provider, backend_model = model.split("/", 1)
    return (provider or None, backend_model or None)


def _fetch_http_status(url: str, timeout: int = 5) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)


def _fetch_sse_status(url: str, timeout: int = 5) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "")
            detail = f"HTTP {response.status}"
            if content_type:
                detail = f"{detail}, content-type={content_type}"
            return (
                200 <= response.status < 400
                and content_type.startswith("text/event-stream"),
                detail,
            )
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)


def _docker_container_running(name: str) -> tuple[bool, str]:
    ok, output = _run_capture(
        ["docker", "inspect", "-f", "{{.State.Running}}", name],
        timeout=5,
    )
    if not ok:
        return False, output or "container not found"
    return output.strip().lower() == "true", output.strip()


def _docker_container_health(name: str) -> tuple[bool, str]:
    ok, output = _run_capture(
        [
            "docker",
            "inspect",
            "-f",
            "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
            name,
        ],
        timeout=5,
    )
    if not ok:
        return False, output or "container not found"
    health = output.strip().lower()
    if health in {"healthy", "none"}:
        return True, health
    return False, health


def cmd_capture_proof_context(output_path: str | None = None) -> int:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    lm_studio_port = os.getenv("LM_STUDIO_PORT", "1234")
    snapshot_id = os.getenv("PROOF_SNAPSHOT_ID", "").strip()
    docker_ok, docker_detail = _run_capture(
        ["docker", "version"], timeout=10
    )
    host_lm_ok, _, host_lm_detail = _fetch_json(
        f"http://localhost:{lm_studio_port}/v1/models",
        timeout=5,
    )

    container_lines: list[str] = []
    if docker_ok:
        for label, container in CORE_CONTAINERS.items():
            running, detail = _docker_container_running(container)
            status = "running" if running else "not running"
            container_lines.append(f"- {label}: {status} ({detail})")
    else:
        container_lines.append(
            "- Core container status skipped because Docker is unavailable."
        )

    verify_env = os.environ.copy()
    verify_env["VERIFY_CYCLES"] = "1"
    verify_env.setdefault("VERIFY_INTERVAL", "1")
    verify_cmd = [
        "python3",
        str(ROOT / "scripts" / "agent_house.py"),
        "verify",
    ]
    verify_completed = subprocess.run(
        verify_cmd,
        check=False,
        capture_output=True,
        text=True,
        env=verify_env,
    )
    verify_output = (
        verify_completed.stdout or verify_completed.stderr or ""
    ).strip()

    host_lm_detail_text = (
        host_lm_detail or f"http://localhost:{lm_studio_port}/v1/models"
    )

    content = "\n".join(
        [
            "# OH_SHOP Proof Context Capture",
            "",
            f"- Captured at: {timestamp}",
            f"- Repo root: {ROOT}",
            f"- Canonical compose file: {COMPOSE_FILE}",
            (
                "- Working snapshot identifier: "
                f"{snapshot_id or 'not provided'}"
            ),
            f"- Proof template path: {PROOF_TEMPLATE}",
            "",
            "## Host checks",
            f"- Docker Engine available: {'yes' if docker_ok else 'no'}",
            f"- Docker detail: {docker_detail or 'n/a'}",
            f"- LM Studio reachable on host: {'yes' if host_lm_ok else 'no'}",
            f"- LM Studio detail: {host_lm_detail_text}",
            "",
            "## Core container snapshot",
            *container_lines,
            "",
            "## Repo-controlled verify run",
            f"- Command: {' '.join(verify_cmd)}",
            "- Environment override: VERIFY_CYCLES=1",
            f"- Exit code: {verify_completed.returncode}",
            "",
            "```text",
            verify_output or "(no output captured)",
            "```",
            "",
            "## Manual proof-run boundary",
            "- This capture does not edit data/openhands.",
            "- This capture does not register MCP into OpenHands.",
            "- This capture does not prove fresh-session tool invocation.",
            "",
        ]
    )

    if output_path:
        destination = Path(output_path)
        if not destination.is_absolute():
            destination = ROOT / destination
        _write_output(destination, content)
        print(f"Wrote proof context capture to {destination}")
    else:
        print(content)
    return 0


def _smoke_markdown(
    *,
    timestamp: str,
    title: str,
    prompt: str,
    task_id: str | None,
    start_task_status: str | None,
    app_conversation_id: str | None,
    sandbox_id: str | None,
    agent_server_url: str | None,
    conversation_url: str | None,
    execution_status: str | None,
    classification: str,
    assistant_text: str,
    observation_text: str,
    detail: str,
) -> str:
    return "\n".join(
        [
            "# OH_SHOP Automated web_research Smoke Test",
            "",
            f"- Captured at: {timestamp}",
            f"- Repo root: {ROOT}",
            "- Command: python3 scripts/agent_house.py "
            "smoke-test-web-research",
            f"- Title: {title}",
            f"- Start task id: {task_id or 'unknown'}",
            f"- Start task status: {start_task_status or 'unknown'}",
            f"- App conversation id: {app_conversation_id or 'unknown'}",
            f"- Sandbox id: {sandbox_id or 'unknown'}",
            f"- Agent server URL: {agent_server_url or 'unknown'}",
            f"- Conversation URL: {conversation_url or 'unknown'}",
            f"- Final execution status: {execution_status or 'unknown'}",
            f"- Outcome classification: {classification}",
            f"- Detail: {detail or 'n/a'}",
            "",
            "## Prompt",
            "",
            "```text",
            prompt,
            "```",
            "",
            "## Assistant Reply",
            "",
            "```text",
            assistant_text or "(no assistant reply captured)",
            "```",
            "",
            "## Tool Observation",
            "",
            "```text",
            observation_text or "(no tool observation captured)",
            "```",
            "",
        ]
    )


def cmd_smoke_test_web_research(
    output_path: str | None = None,
    prompt: str | None = None,
    timeout_seconds: int | None = None,
) -> int:
    prompt_text = (prompt or DEFAULT_WEB_RESEARCH_PROOF_PROMPT).strip()
    timeout_seconds = timeout_seconds or int(
        os.getenv("SMOKE_TEST_TIMEOUT", "420")
    )
    post_observation_grace = int(
        os.getenv("SMOKE_TEST_POST_OBSERVATION_GRACE", "240")
    )
    post_reply_grace = int(os.getenv("SMOKE_TEST_POST_REPLY_GRACE", "30"))
    deadline = time.monotonic() + timeout_seconds
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    title = f"OH_SHOP OpenHands proof {time.strftime('%Y%m%d_%H%M%S')}"

    def emit_result(
        classification: str,
        detail: str,
        *,
        success: bool,
        task_id: str | None = None,
        start_task_status: str | None = None,
        app_conversation_id: str | None = None,
        sandbox_id: str | None = None,
        agent_server_url: str | None = None,
        conversation_url: str | None = None,
        execution_status: str | None = None,
        assistant_text: str = "",
        observation_text: str = "",
    ) -> int:
        content = _smoke_markdown(
            timestamp=timestamp,
            title=title,
            prompt=prompt_text,
            task_id=task_id,
            start_task_status=start_task_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
            conversation_url=conversation_url,
            execution_status=execution_status,
            classification=classification,
            assistant_text=assistant_text,
            observation_text=observation_text,
            detail=detail,
        )
        if output_path:
            destination = Path(output_path)
            if not destination.is_absolute():
                destination = ROOT / destination
            _write_output(destination, content)
            print(f"Wrote smoke test artifact to {destination}")
        print(content)
        sandboxes_ok, sandboxes_detail = _remove_openhands_sandboxes()
        cleanup_status = "PASS" if sandboxes_ok else "FAIL"
        print(
            f"[{cleanup_status}] OpenHands sandbox cleanup after smoke test - "
            f"{sandboxes_detail}"
        )
        return 0 if success else 1

    start_payload = {
        "title": title,
        "initial_message": {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text}
            ],
            "run": True,
        },
    }
    ok, start_task_payload, detail = _request_json_any(
        f"{OPENHANDS_URL}/api/v1/app-conversations",
        method="POST",
        payload=start_payload,
        timeout=15,
    )
    if not ok or not isinstance(start_task_payload, dict):
        return emit_result(
            "integration failure",
            f"failed to start app conversation: {detail}",
            success=False,
        )

    task_id = start_task_payload.get("id")
    if not isinstance(task_id, str) or not task_id:
        return emit_result(
            "integration failure",
            f"start task id missing from response: {start_task_payload!r}",
            success=False,
        )

    ready_task: dict[str, Any] | None = None
    last_status = str(start_task_payload.get("status") or "")
    while time.monotonic() < deadline:
        quoted_task_id = urllib.parse.quote(task_id)
        ok, poll_payload, detail = _request_json_any(
            f"{OPENHANDS_URL}/api/v1/app-conversations/start-tasks?ids="
            f"{quoted_task_id}",
            timeout=10,
        )
        if ok and isinstance(poll_payload, list) and poll_payload:
            candidate = poll_payload[0]
            if isinstance(candidate, dict):
                last_status = str(candidate.get("status") or "")
                if last_status == "READY":
                    ready_task = candidate
                    break
                if last_status in {
                    "FAILED",
                    "ERROR",
                    "CANCELLED",
                    "CANCELED",
                }:
                    msg = "start task ended in unexpected status " + repr(
                        last_status
                    )
                    return emit_result(
                        "integration failure",
                        msg,
                        success=False,
                        task_id=task_id,
                        start_task_status=last_status,
                    )
        time.sleep(2)

    if ready_task is None:
        return emit_result(
            "integration failure",
            (
                "timed out waiting for app conversation "
                "start task to become READY"
            ),
            success=False,
            task_id=task_id,
            start_task_status=last_status,
        )

    app_conversation_id = ready_task.get("app_conversation_id")
    sandbox_id = (
        ready_task.get("sandbox_id")
        if isinstance(ready_task.get("sandbox_id"), str)
        else None
    )
    agent_server_url = (
        ready_task.get("agent_server_url")
        if isinstance(
            ready_task.get("agent_server_url"), str
        )
        else None
    )
    if (
        not isinstance(app_conversation_id, str)
        or not app_conversation_id
    ):
        return emit_result(
            "integration failure",
            "READY start task did not include app_conversation_id",
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
        )

    app_record: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        ok, search_payload, detail = _request_json_any(
            (
                f"{OPENHANDS_URL}/api/v1/app-conversations"
                "/search?limit=100"
            ),
            timeout=10,
        )
        if ok and isinstance(search_payload, dict):
            items = search_payload.get("items")
            if isinstance(items, list):
                for item in items:
                    if (
                        isinstance(item, dict)
                        and item.get("id") == app_conversation_id
                    ):
                        app_record = item
                        break
        if app_record is not None:
            break
        time.sleep(1)

    if app_record is None:
        return emit_result(
            "integration failure",
            (
                "app conversation record was not available "
                "after start task became READY"
            ),
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
        )

    session_api_key = app_record.get("session_api_key")
    conversation_url = app_record.get("conversation_url")
    if (
        not isinstance(session_api_key, str)
        or not session_api_key
    ):
        return emit_result(
            "integration failure",
            "session_api_key missing from app conversation record",
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
        )
    if (
        not isinstance(conversation_url, str)
        or not conversation_url
    ):
        return emit_result(
            "integration failure",
            "conversation_url missing from app conversation record",
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
        )

    conversation_api_url = conversation_url.replace(
        "http://localhost", "http://127.0.0.1"
    )
    sandbox_headers = {"X-Session-API-Key": session_api_key}
    execution_status = None
    events_payload: dict[str, Any] | None = None
    events_detail = ""
    tool_action: dict[str, Any] | None = None
    observation_event: dict[str, Any] | None = None
    assistant_text = ""
    observation_text = ""
    observation_seen_at: float | None = None
    assistant_seen_at: float | None = None

    while True:
        now = time.monotonic()
        effective_deadline = deadline
        if observation_seen_at is not None:
            effective_deadline = max(
                effective_deadline,
                observation_seen_at + post_observation_grace,
            )
        if assistant_seen_at is not None:
            effective_deadline = max(
                effective_deadline,
                assistant_seen_at + post_reply_grace,
            )
        if now >= effective_deadline:
            break

        ok, live_conversation, detail = _request_json_any(
            conversation_api_url,
            headers=sandbox_headers,
            timeout=15,
        )
        if ok and isinstance(live_conversation, dict):
            execution_status = live_conversation.get("execution_status")
            if execution_status == "finished":
                break
            if execution_status in {"error", "failed"}:
                return emit_result(
                    "integration failure",
                    (
                        f"sandbox conversation ended in "
                        f"{execution_status!r}"
                    ),
                    success=False,
                    task_id=task_id,
                    start_task_status=last_status,
                    app_conversation_id=app_conversation_id,
                    sandbox_id=sandbox_id,
                    agent_server_url=agent_server_url,
                    conversation_url=conversation_url,
                    execution_status=str(execution_status),
                )

        ok, payload, detail = _fetch_conversation_events(
            app_conversation_id=app_conversation_id,
            conversation_api_url=conversation_api_url,
            sandbox_headers=sandbox_headers,
            timeout=15,
        )
        if ok and isinstance(payload, dict):
            events_payload = payload
            items = payload.get("items")
            (
                tool_action,
                observation_event,
                assistant_text,
                observation_text,
            ) = _extract_web_research_events(items)
            if observation_event is not None and observation_seen_at is None:
                observation_seen_at = time.monotonic()
            if assistant_text and assistant_seen_at is None:
                assistant_seen_at = time.monotonic()

            observation_error = bool(
                isinstance(observation_event, dict)
                and observation_event.get(
                    "observation", {}
                ).get("is_error")
            )
            if (
                tool_action
                and observation_event
                and not observation_error
                and assistant_text
            ):
                if execution_status == "finished":
                    return emit_result(
                        "success",
                        (
                            "fresh-session API smoke test captured "
                            "tool action, successful observation, "
                            "assistant reply, and finished execution"
                        ),
                        success=True,
                        task_id=task_id,
                        start_task_status=last_status,
                        app_conversation_id=app_conversation_id,
                        sandbox_id=sandbox_id,
                        agent_server_url=agent_server_url,
                        conversation_url=conversation_url,
                        execution_status=str(execution_status),
                        assistant_text=assistant_text,
                        observation_text=observation_text,
                    )
        else:
            events_detail = detail

        if execution_status == "finished":
            break

        time.sleep(2)

    for _ in range(5):
        ok, payload, detail = _fetch_conversation_events(
            app_conversation_id=app_conversation_id,
            conversation_api_url=conversation_api_url,
            sandbox_headers=sandbox_headers,
            timeout=15,
        )
        if ok and isinstance(payload, dict):
            events_payload = payload
            break
        events_detail = detail
        time.sleep(1)

    if events_payload is None:
        return emit_result(
            "integration failure",
            f"failed to fetch sandbox events: {events_detail}",
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
            conversation_url=conversation_url,
            execution_status=str(execution_status),
        )

    items = events_payload.get("items")
    if not isinstance(items, list):
        return emit_result(
            "integration failure",
            "sandbox events response did not include an items list",
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
            conversation_url=conversation_url,
            execution_status=str(execution_status),
        )

    (
        tool_action,
        observation_event,
        assistant_text,
        observation_text,
    ) = _extract_web_research_events(items)

    if tool_action is None:
        detail = (
            "timed out before a real web_research tool "
            "action event was observed"
        )
        if execution_status == "finished":
            detail = (
                "conversation finished without a real "
                "web_research tool action event"
            )
        return emit_result(
            "model-behavior failure",
            detail,
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
            conversation_url=conversation_url,
            execution_status=str(execution_status),
            assistant_text=assistant_text,
        )

    if (
        observation_event is None
        or observation_event.get(
            "observation", {}
        ).get("is_error")
    ):
        detail = (
            "web_research tool observation was missing "
            "or marked as an error"
        )
        if observation_event is None and execution_status != "finished":
            detail = (
                "timed out after the web_research action "
                "but before a successful observation was captured"
            )
        return emit_result(
            "provider/dependency failure",
            detail,
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
            conversation_url=conversation_url,
            execution_status=str(execution_status),
            assistant_text=assistant_text,
            observation_text=observation_text,
        )

    if not assistant_text:
        detail = (
            "conversation finished after the tool observation "
            "but no final assistant reply was captured"
        )
        classification = "model-behavior failure"
        if execution_status != "finished":
            detail = (
                "timed out after a successful tool observation "
                "while waiting for the final assistant reply"
            )
            classification = "integration failure"
        return emit_result(
            classification,
            detail,
            success=False,
            task_id=task_id,
            start_task_status=last_status,
            app_conversation_id=app_conversation_id,
            sandbox_id=sandbox_id,
            agent_server_url=agent_server_url,
            conversation_url=conversation_url,
            execution_status=str(execution_status),
            observation_text=observation_text,
        )

    detail = (
        "fresh-session API smoke test captured tool action, "
        "successful observation, and assistant reply; "
        f"execution status remained {execution_status!r}"
    )
    if execution_status == "finished":
        detail = (
            "fresh-session API smoke test captured "
            "tool action, successful observation, assistant reply, "
            "and finished execution"
        )

    return emit_result(
        "success",
        detail,
        success=True,
        task_id=task_id,
        start_task_status=last_status,
        app_conversation_id=app_conversation_id,
        sandbox_id=sandbox_id,
        agent_server_url=agent_server_url,
        conversation_url=conversation_url,
        execution_status=str(execution_status),
        assistant_text=assistant_text,
        observation_text=observation_text,
    )


def cmd_verify() -> int:
    lm_studio_port = os.getenv("LM_STUDIO_PORT", "1234")
    cycles = int(os.getenv("VERIFY_CYCLES", "6"))
    interval_seconds = int(os.getenv("VERIFY_INTERVAL", "10"))
    if cycles < 1:
        raise ValueError("VERIFY_CYCLES must be >= 1")
    if interval_seconds < 1:
        raise ValueError("VERIFY_INTERVAL must be >= 1")
    required_failures = 0
    lm_host_url = f"http://localhost:{lm_studio_port}/v1/models"
    lm_docker_url = (
        f"http://host.docker.internal:{lm_studio_port}/v1/models"
    )
    expected_lm_base_url = lm_docker_url.removesuffix("/models")

    def print_result(
        status: str,
        label: str,
        detail: str = "",
    ) -> None:
        suffix = f" - {detail}" if detail else ""
        print(f"  [{status}] {label}{suffix}")

    for cycle in range(1, cycles + 1):
        cycle_failures = 0
        print(f"-- verify cycle {cycle}/{cycles} --")

        def cycle_require(ok: bool, label: str, detail: str = "") -> None:
            nonlocal cycle_failures
            if ok:
                print_result("PASS", label, detail)
            else:
                cycle_failures += 1
                print_result("FAIL", label, detail)

        print("Layer 1 - container/process up")
        ok, detail = _run_capture(["docker", "version"], timeout=10)
        docker_detail_msg = detail or "docker version ok"
        cycle_require(ok, "Docker Engine available", docker_detail_msg)

        compose_exists = COMPOSE_FILE.exists()
        cycle_require(
            compose_exists,
            "Canonical compose file present",
            str(COMPOSE_FILE),
        )

        containers_running = True
        for label, container in CORE_CONTAINERS.items():
            running, detail = _docker_container_running(container)
            containers_running &= running
            cycle_require(
                running, f"{label} container running", detail
            )

        print("Layer 2 - service health endpoint responds")
        service_checks = [
            ("OpenHands", "http://localhost:3000"),
            ("OpenWebUI", "http://localhost:3001"),
            ("SearxNG", "http://localhost:3002/"),
            ("oh-browser-mcp health", "http://localhost:3010/health"),
        ]
        if not containers_running:
            for label, _ in service_checks:
                print_result(
                    "UNPROVEN",
                    label,
                    (
                        "skipped because required containers "
                        "are not all running"
                    ),
                )
        else:
            for label, url in service_checks:
                ok, detail = _fetch_http_status(url, timeout=5)
                cycle_require(ok, label, detail)

            for label, container in CORE_CONTAINERS.items():
                ok, detail = _docker_container_health(container)
                cycle_require(
                    ok, f"{label} container health state", detail
                )

        print("Layer 3 - provider/search dependencies reachable")
        host_lm_ok, host_lm_payload, host_lm_detail = _fetch_json(
            lm_host_url, timeout=5
        )
        cycle_require(
            host_lm_ok,
            "LM Studio reachable on host",
            host_lm_detail or lm_host_url,
        )
        available_model_ids: list[str] = []
        if host_lm_ok and host_lm_payload is not None:
            data = host_lm_payload.get("data")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        model_id = item.get("id")
                        if isinstance(model_id, str):
                            available_model_ids.append(model_id)

        dependency_exec_checks = [
            (
                "LM Studio route from OpenHands",
                "openhands-app",
                [
                    "curl",
                    "-sf",
                    "-o",
                    "/dev/null",
                    "--max-time",
                    "5",
                    lm_docker_url,
                ],
            ),
            (
                "LM Studio route from OpenWebUI",
                "open-webui",
                [
                    "curl",
                    "-sf",
                    "-o",
                    "/dev/null",
                    "--max-time",
                    "5",
                    lm_docker_url,
                ],
            ),
            (
                "LM Studio route from oh-browser-mcp",
                "oh-browser-mcp",
                [
                    "curl",
                    "-sf",
                    "-o",
                    "/dev/null",
                    "--max-time",
                    "5",
                    lm_docker_url,
                ],
            ),
            (
                "SearxNG route from oh-browser-mcp",
                "oh-browser-mcp",
                [
                    "curl",
                    "-sf",
                    "-o",
                    "/dev/null",
                    "--max-time",
                    "5",
                    "http://searxng:8080/",
                ],
            ),
        ]
        for label, container, inner_cmd in dependency_exec_checks:
            running, detail = _docker_container_running(container)
            if not running:
                print_result(
                    "UNPROVEN",
                    label,
                    f"skipped because container is not running ({detail})",
                )
                continue
            ok, detail = _run_capture(
                ["docker", "exec", container, *inner_cmd],
                timeout=10,
            )
            inner_detail = detail or (
                "reachable" if ok else "dependency route check failed"
            )
            cycle_require(
                ok,
                label,
                inner_detail,
            )

        sandbox_ok, sandbox_detail = _run_capture(
            [
                "docker",
                "run",
                "--rm",
                "--add-host",
                "host.docker.internal:host-gateway",
                "python:3.11-alpine",
                "python",
                "-c",
                (
                    "import socket; "
                    "s=socket.create_connection("
                    "('host.docker.internal', 3000), 5); "
                    "s.close()"
                ),
            ],
            timeout=20,
        )
        cycle_require(
            sandbox_ok,
            "OpenHands route from sandbox bridge",
            sandbox_detail or "reachable",
        )

        print(
            "Layer 4 - MCP server endpoint reachable "
            "and readiness reported"
        )
        mcp_health_ok, mcp_health_payload, mcp_health_detail = (
            _fetch_json("http://localhost:3010/health", timeout=5)
        )
        if mcp_health_ok and mcp_health_payload is not None:
            cycle_require(
                True,
                "oh-browser-mcp /health reachable",
                (
                    f"ok={mcp_health_payload.get('ok')} "
                    f"ready={mcp_health_payload.get('ready')}"
                ),
            )
        else:
            cycle_require(
                False,
                "oh-browser-mcp /health reachable",
                mcp_health_detail,
            )

        mcp_ready_ok, mcp_ready_payload, mcp_ready_detail = (
            _fetch_json("http://localhost:3010/ready", timeout=5)
        )
        if mcp_ready_ok and mcp_ready_payload is not None:
            cycle_require(
                bool(mcp_ready_payload.get("ready")),
                (
                    "oh-browser-mcp /ready "
                    "reports research readiness"
                ),
                mcp_ready_payload.get("readiness", "ready"),
            )
        else:
            cycle_require(
                False,
                (
                    "oh-browser-mcp /ready "
                    "reports research readiness"
                ),
                mcp_ready_detail,
            )

        sse_ok, sse_detail = _fetch_sse_status(
            "http://localhost:3010/sse",
            timeout=5,
        )
        cycle_require(
            sse_ok,
            "oh-browser-mcp SSE endpoint reachable",
            sse_detail or ("reachable" if sse_ok else "SSE handshake failed"),
        )

        sandbox_mcp_ok, sandbox_mcp_detail = _run_capture(
            [
                "docker",
                "run",
                "--rm",
                "--add-host",
                "host.docker.internal:host-gateway",
                "curlimages/curl:8.8.0",
                "-I",
                "--max-time",
                "5",
                "http://host.docker.internal:3010/sse",
            ],
            timeout=20,
        )
        cycle_require(
            sandbox_mcp_ok,
            "oh-browser-mcp route from sandbox bridge",
            sandbox_mcp_detail or "reachable",
        )

        print(
            "Layer 5 - OpenHands runtime settings alignment"
        )
        patch_check_ok, patch_check_detail = _run_capture(
            [
                "docker",
                "exec",
                "openhands-app",
                "python",
                "-c",
                (
                    "from pathlib import Path; "
                    f"text = Path("
                    f"{OPENHANDS_TOOL_CALL_PATCH_TARGET!r}"
                    ").read_text(); "
                    "raise SystemExit(0 if "
                    '"if model and \'openhands-lm\' in model:\\n'
                    '            llm_kwargs[\'native_tool_calling\']'
                    ' = False" '
                    "in text else 1)"
                ),
            ],
            timeout=10,
        )
        cycle_require(
            patch_check_ok,
            (
                "OpenHands V1 tool-calling "
                "compatibility patch present"
            ),
            patch_check_detail or OPENHANDS_TOOL_CALL_PATCH_TARGET,
        )

        live_settings_ok, live_settings_payload, (
            live_settings_detail
        ) = _fetch_json(
            "http://localhost:3000/api/settings",
            timeout=5,
        )
        if not live_settings_ok or live_settings_payload is None:
            cycle_require(
                False,
                "OpenHands live settings API reachable",
                live_settings_detail,
            )
        else:
            cycle_require(
                True,
                "OpenHands live settings API reachable",
                "/api/settings",
            )

            live_base_url = live_settings_payload.get("llm_base_url")
            cycle_require(
                live_base_url == expected_lm_base_url,
                (
                    "OpenHands live LLM base URL matches "
                    "LM Studio route"
                ),
                (
                    f"current={live_base_url!r} "
                    f"expected={expected_lm_base_url!r}"
                ),
            )

            live_model = live_settings_payload.get("llm_model")
            provider, backend_model = _split_provider_model(
                live_model
            )
            provider_ok = provider == "openai"
            cycle_require(
                provider_ok,
                (
                    "OpenHands live model uses required "
                    "provider prefix"
                ),
                (
                    f"current={live_model!r} "
                    "expected_prefix='openai/'"
                ),
            )

            model_ok = (
                isinstance(backend_model, str)
                and backend_model in available_model_ids
            )
            available_models_detail = (
                ", ".join(available_model_ids) or "none reported"
            )
            cycle_require(
                model_ok,
                (
                    "OpenHands live model ID exists in "
                    "LM Studio /v1/models"
                ),
                (
                    f"current={live_model!r}; "
                    f"backend_model={backend_model!r}; "
                    f"available={available_models_detail}"
                ),
            )

            sse_servers = live_settings_payload.get(
                "mcp_config", {}
            ).get("sse_servers", [])
            first_sse_url = None
            if isinstance(sse_servers, list) and sse_servers:
                first_entry = sse_servers[0]
                if isinstance(first_entry, dict):
                    first_sse_url = first_entry.get("url")
            cycle_require(
                first_sse_url == EXPECTED_MCP_URL,
                (
                    "OpenHands live MCP URL matches "
                    "sandbox-reachable path"
                ),
                (
                    f"current={first_sse_url!r} "
                    f"expected={EXPECTED_MCP_URL!r}"
                ),
            )

        persisted_ok, persisted_payload, persisted_detail = (
            _load_json_file(OPENHANDS_SETTINGS_FILE)
        )
        if not persisted_ok or persisted_payload is None:
            print_result(
                "UNPROVEN",
                "Persisted settings file comparison",
                persisted_detail,
            )
        else:
            persisted_base_url = persisted_payload.get("llm_base_url")
            persisted_model = persisted_payload.get("llm_model")
            live_base_url = None
            live_model = None
            if live_settings_payload is not None:
                live_base_url = live_settings_payload.get("llm_base_url")
                live_model = live_settings_payload.get("llm_model")
            drift_messages: list[str] = []
            if live_base_url != persisted_base_url:
                drift_messages.append(
                    (
                        f"llm_base_url live={live_base_url!r} "
                        f"persisted={persisted_base_url!r}"
                    )
                )
            if live_model != persisted_model:
                drift_messages.append(
                    (
                        f"llm_model live={live_model!r} "
                        f"persisted={persisted_model!r}"
                    )
                )
            if drift_messages:
                print_result(
                    "WARN",
                    (
                        "Persisted settings file drift from "
                        "live runtime settings"
                    ),
                    "; ".join(drift_messages),
                )
            else:
                print_result(
                    "PASS",
                    (
                        "Persisted settings file matches "
                        "live runtime settings"
                    ),
                    str(OPENHANDS_SETTINGS_FILE),
                )

        print("Layer 6 - fresh-session tool invocation")
        print_result(
            "UNPROVEN",
            "Fresh-session web_research invocation",
            (
                "requires manual MCP registration and "
                "a new OpenHands session; verify only proves "
                "infrastructure and readiness boundaries"
            ),
        )

        if cycle_failures:
            required_failures += cycle_failures

        if cycle < cycles:
            time.sleep(interval_seconds)

    print()
    print("Verification summary:")
    if required_failures == 0:
        print(
            "  PASS: layers 1-5 passed for all cycles. "
            "Layer 6 remains intentionally unproven."
        )
        return 0

    print(
        "  FAIL: one or more required checks in layers 1-5 failed. "
        "Layer 6 remains intentionally unproven."
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent House helper")
    parser.add_argument(
        "command",
        choices=[
            "up",
            "down",
            "cleanup-sandboxes",
            "logs",
            "verify",
            "capture-proof-context",
            "smoke-test-web-research",
            "reconcile-chats",
            "monitor-chats",
        ],
    )
    parser.add_argument(
        "--output",
        help="Optional output path for proof capture commands.",
    )
    parser.add_argument(
        "--prompt",
        help="Optional prompt override for smoke-test-web-research.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Optional timeout in seconds for smoke-test-web-research.",
    )
    args = parser.parse_args()

    if args.command == "up":
        return cmd_up()
    if args.command == "down":
        return cmd_down()
    if args.command == "cleanup-sandboxes":
        ok, detail = _remove_openhands_sandboxes()
        print(detail)
        return 0 if ok else 1
    if args.command == "logs":
        return cmd_logs()
    if args.command == "verify":
        return cmd_verify()
    if args.command == "capture-proof-context":
        return cmd_capture_proof_context(args.output)
    if args.command == "smoke-test-web-research":
        return cmd_smoke_test_web_research(
            args.output,
            args.prompt,
            args.timeout,
        )
    if args.command == "reconcile-chats":
        return cmd_reconcile_chats()
    if args.command == "monitor-chats":
        return cmd_monitor_chats()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
