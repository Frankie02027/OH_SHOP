from __future__ import annotations

import asyncio
import importlib
import json
import logging
import tempfile
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import get_settings
from .downloads import ensure_download_dir

logger = logging.getLogger(__name__)

TOOL_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "minLength": 1,
            "description": (
                "Use the user's original external target. Preserve exact "
                "project names, filenames, artifact names, version strings, "
                "requested file types, and path fragments instead of "
                "broadening them away. If the user did not provide a URL, "
                "do not invent one."
            ),
        },
        "max_results": {
            "type": ["integer", "string"],
            "minimum": 1,
            "maximum": 20,
            "default": 5,
        },
        "max_pages": {
            "type": ["integer", "string"],
            "minimum": 1,
            "maximum": 40,
            "default": 8,
        },
        "max_steps": {
            "type": ["integer", "string"],
            "minimum": 1,
            "maximum": 200,
            "default": 40,
        },
        "download": {
            "type": ["boolean", "string"],
            "default": True,
        },
        "allowed_domains": {
            "type": ["array", "null"],
            "items": {"type": "string"},
            "default": None,
        },
        "seed_urls": {
            "type": ["array", "null"],
            "items": {"type": "string"},
            "default": None,
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}

TOOL_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "sources": {"type": "array", "items": {"type": "string"}},
        "quotes": {"type": "array", "items": {"type": "string"}},
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "sha256": {"type": "string"},
                    "bytes": {"type": "integer"},
                },
                "required": ["path", "sha256", "bytes"],
                "additionalProperties": False,
            },
        },
        "trace": {"type": "object"},
    },
    "required": ["answer", "sources", "quotes", "artifacts", "trace"],
    "additionalProperties": True,
}

TOOL_NAMES = ("web_research", "web_re_search")

_runtime_lock = asyncio.Lock()
_runtime: dict[str, Any] | None = None


def _configure_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "oh-browser-mcp.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )


def _parse_positive_int(
    name: str,
    value: Any,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return parsed


def _validate_web_research_input(arguments: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")

    allowed_keys = {
        "query",
        "max_results",
        "max_pages",
        "max_steps",
        "download",
        "allowed_domains",
        "seed_urls",
    }
    extra = sorted(set(arguments.keys()) - allowed_keys)
    if extra:
        raise ValueError(f"Unexpected argument(s): {', '.join(extra)}")

    query = str(arguments.get("query", "")).strip()
    if not query:
        raise ValueError("query is required and must be a non-empty string.")

    max_results = _parse_positive_int(
        "max_results", arguments.get("max_results"), 5, 1, 20
    )
    max_pages = _parse_positive_int(
        "max_pages", arguments.get("max_pages"), 8, 1, 40
    )
    max_steps = _parse_positive_int(
        "max_steps", arguments.get("max_steps"), 40, 1, 200
    )

    download = arguments.get("download", True)
    if isinstance(download, str):
        normalized = download.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            download = True
        elif normalized in {"false", "0", "no", "n"}:
            download = False
        else:
            raise ValueError("download must be a boolean.")
    elif not isinstance(download, bool):
        raise ValueError("download must be a boolean.")

    allowed_domains = arguments.get("allowed_domains")
    if allowed_domains is not None:
        if not isinstance(allowed_domains, list) or not all(
            isinstance(item, str) for item in allowed_domains
        ):
            raise ValueError(
                "allowed_domains must be null or an array of strings."
            )

    seed_urls = arguments.get("seed_urls")
    if seed_urls is not None:
        if not isinstance(seed_urls, list) or not all(
            isinstance(item, str) for item in seed_urls
        ):
            raise ValueError(
                "seed_urls must be null or an array of strings."
            )

    return {
        "query": query,
        "max_results": max_results,
        "max_pages": max_pages,
        "max_steps": max_steps,
        "download": download,
        "allowed_domains": allowed_domains,
        "seed_urls": seed_urls,
    }


def _build_runtime() -> dict[str, Any]:
    from mcp.server.lowlevel import Server
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool

    mcp_server = Server(name="oh-browser-mcp")
    sse = SseServerTransport("/messages/")

    @mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        tools: list[Tool] = []
        for name in TOOL_NAMES:
            description = (
                "Use this for public internet tasks: search the web, open "
                "sites, follow links across multiple pages, read external "
                "documentation, inspect GitHub projects, and download "
                "files with a real browser. Prefer this tool when the "
                "user asks for anything from a website, repository, "
                "release asset, package, file, archive, or other external "
                "resource. Do not search the local workspace for files "
                "that are supposed to come from the internet unless the "
                "user explicitly asks about local files. When searching, "
                "keep the user's named project, artifact, filename, file "
                "extension, path fragment, and version clues intact instead "
                "of broadening them away. If the user asks for a specific "
                "file, archive, checksum, or versioned download, include "
                "those exact clues in the query arguments."
            )
            if name != "web_research":
                description += (
                    " Compatibility alias for web_research."
                )
            tools.append(
                Tool(
                    name=name,
                    description=description,
                    inputSchema=TOOL_INPUT_SCHEMA,
                    outputSchema=TOOL_OUTPUT_SCHEMA,
                )
            )
        return tools

    @mcp_server.call_tool()
    async def call_tool(
        name: str,
        arguments: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if name not in TOOL_NAMES:
            raise ValueError(f"Unknown tool: {name}")

        payload = _validate_web_research_input(arguments or {})
        from .research import run_web_research

        return await run_web_research(
            query=payload["query"],
            max_results=payload["max_results"],
            max_pages=payload["max_pages"],
            max_steps=payload["max_steps"],
            download=payload["download"],
            allowed_domains=payload["allowed_domains"],
            seed_urls=payload["seed_urls"],
        )

    return {"server": mcp_server, "sse": sse}


async def _get_runtime() -> dict[str, Any]:
    global _runtime
    if _runtime is not None:
        return _runtime

    async with _runtime_lock:
        if _runtime is None:
            _runtime = _build_runtime()
    return _runtime


def create_app() -> Any:
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Mount, Route
    from starlette.types import Receive, Scope, Send

    settings = get_settings()
    ensure_download_dir(settings.download_dir)
    _configure_logging(settings.log_dir)

    def _check_import(module_name: str) -> dict[str, Any]:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True}

    def _check_url(url: str, timeout: int = 3) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return {"ok": 200 <= response.status < 400, "status": response.status}
        except urllib.error.HTTPError as exc:
            return {"ok": False, "status": exc.code, "error": f"HTTP {exc.code}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _check_searxng(base_url: str) -> dict[str, Any]:
        service_status = _check_url(f"{base_url}/", timeout=3)
        result: dict[str, Any] = {
            "configured": bool(base_url),
            "url": base_url,
            "ok": bool(service_status.get("ok")),
            "service": service_status,
        }

        query_url = (
            f"{base_url}/search?"
            + urllib.parse.urlencode({"q": "agent house", "format": "json"})
        )
        query_probe: dict[str, Any] = {"url": query_url}
        try:
            with urllib.request.urlopen(query_url, timeout=12) as response:
                body = response.read().decode("utf-8", errors="replace")
                payload = json.loads(body)
                raw_results = payload.get("results")
                raw_unresponsive = payload.get("unresponsive_engines")
                query_probe.update(
                    {
                        "ok": True,
                        "status": response.status,
                        "result_count": len(raw_results)
                        if isinstance(raw_results, list)
                        else None,
                        "unresponsive_engines": raw_unresponsive
                        if isinstance(raw_unresponsive, list)
                        else [],
                    }
                )
        except urllib.error.HTTPError as exc:
            query_probe.update({"ok": False, "status": exc.code, "error": f"HTTP {exc.code}"})
        except Exception as exc:
            query_probe.update({"ok": False, "error": str(exc)})

        result["search_probe"] = query_probe
        if not result["ok"] and query_probe.get("ok"):
            result["ok"] = True
        return result

    async def _readiness_status() -> tuple[bool, dict[str, Any]]:
        download_dir = settings.download_dir
        checks: dict[str, Any] = {
            "download_dir": {
                "path": str(download_dir),
                "exists": download_dir.exists(),
                "is_dir": download_dir.is_dir(),
                "writable": False,
            },
            "imports": {},
            "dependencies": {
                "searxng": {},
                "lm_studio": {
                    "configured": bool(settings.llm_base_url),
                    "url": settings.llm_base_url,
                },
            },
            "mcp_transport": {
                "sse_path": "/sse",
                "messages_path": "/messages/",
            },
        }
        notes = [
            "A healthy process is not the same as OpenHands MCP registration.",
            "A ready MCP server is not the same as a successful fresh-session tool call.",
        ]

        if not download_dir.exists() or not download_dir.is_dir():
            payload = {
                "ok": False,
                "ready": False,
                "readiness": "blocked",
                "reason": "download_dir_missing",
                "checks": checks,
                "notes": notes,
            }
            return False, payload

        try:
            with tempfile.NamedTemporaryFile(
                dir=download_dir,
                prefix=".healthcheck-",
                delete=True,
            ):
                pass
        except Exception:
            payload = {
                "ok": False,
                "ready": False,
                "readiness": "blocked",
                "reason": "download_dir_not_writable",
                "checks": checks,
                "notes": notes,
            }
            return False, payload

        checks["download_dir"]["writable"] = True

        checks["imports"]["playwright.async_api"] = _check_import(
            "playwright.async_api"
        )
        checks["imports"]["langchain_openai"] = _check_import("langchain_openai")
        browser_use_import = _check_import("browser_use")
        browser_use_import["optional"] = True
        checks["imports"]["browser_use"] = browser_use_import

        searxng_status = _check_searxng(settings.searxng_url)
        lm_studio_status = _check_url(f"{settings.llm_base_url}/models")
        checks["dependencies"]["searxng"].update(searxng_status)
        checks["dependencies"]["lm_studio"].update(lm_studio_status)

        ready = (
            checks["download_dir"]["writable"]
            and checks["imports"]["playwright.async_api"]["ok"]
            and checks["imports"]["langchain_openai"]["ok"]
            and checks["dependencies"]["searxng"]["ok"]
            and checks["dependencies"]["lm_studio"]["ok"]
        )

        readiness = "ready" if ready else "degraded"
        summary = (
            "web_research dependencies reachable"
            if ready
            else "service is up but web_research is not fully ready"
        )
        search_probe = checks["dependencies"]["searxng"].get("search_probe", {})
        if ready and isinstance(search_probe, dict) and not search_probe.get("ok"):
            notes.append(
                "SearxNG service is reachable, but the live search probe is currently degraded."
            )
        elif ready and isinstance(search_probe, dict):
            unresponsive = search_probe.get("unresponsive_engines")
            if isinstance(unresponsive, list) and unresponsive:
                notes.append(
                    "SearxNG is reachable, but some upstream public engines are throttled or timing out."
                )
        payload = {
            "ok": True,
            "ready": ready,
            "readiness": readiness,
            "summary": summary,
            "checks": checks,
            "notes": notes,
        }
        return True, payload

    async def handle_sse(request: Request) -> Response:
        runtime = await _get_runtime()
        sse = runtime["sse"]
        mcp_server = runtime["server"]
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as streams:  # type: ignore[attr-defined]
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )
        return Response()

    async def handle_messages(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        runtime = await _get_runtime()
        sse = runtime["sse"]
        await sse.handle_post_message(scope, receive, send)

    async def health(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "ok": True,
                "status": "up",
                "service": "oh-browser-mcp",
            },
            status_code=200,
        )

    async def ready(_: Request) -> JSONResponse:
        ok, payload = await _readiness_status()
        status_code = 200 if ok and payload.get("ready") else 503
        return JSONResponse(payload, status_code=status_code)

    return Starlette(
        routes=[
            Route("/health", endpoint=health, methods=["GET"]),
            Route("/ready", endpoint=ready, methods=["GET"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=handle_messages),
        ]
    )


def main() -> None:
    import socket

    settings = get_settings()
    # Pre-bind the port before heavy imports/app construction so early
    # health checks
    # queue instead of being reset during process warm-up.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", settings.mcp_port))
    server_socket.listen(2048)
    server_socket.setblocking(False)

    from uvicorn import Config, Server

    app = create_app()
    config = Config(app=app, host="0.0.0.0", port=settings.mcp_port)
    server = Server(config=config)
    server.run(sockets=[server_socket])


if __name__ == "__main__":
    main()
