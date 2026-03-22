from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from .config import get_settings
from .searx import SearxSearchError, _query_profile, search_searxng

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .browse import BrowserAutomationBlockedError


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _extract_urls(text: str) -> list[str]:
    matches = re.findall(r"https?://[^\s<>()\"']+", text or "", flags=re.IGNORECASE)
    cleaned: list[str] = []
    for match in matches:
        candidate = match.rstrip(".,);]}>\"'")
        if candidate:
            cleaned.append(candidate)
    return _dedupe_keep_order(cleaned)


def _url_allowed(url: str, allowed_domains: list[str] | None) -> bool:
    if not allowed_domains:
        return True
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    normalized = []
    for domain in allowed_domains:
        cleaned = domain.strip().lower()
        if not cleaned:
            continue
        if "://" in cleaned:
            cleaned = urlparse(cleaned).hostname or cleaned
        cleaned = cleaned.lstrip(".")
        if cleaned:
            normalized.append(cleaned)
    return any(
        host == domain or host.endswith(f".{domain}")
        for domain in normalized
    )


def _build_answer(
    query: str,
    sources: list[str],
    quotes: list[str],
    artifacts: list[dict[str, Any]],
) -> str:
    if not sources:
        return f"No browsable sources were found for: {query}"

    lines = [
        f"Web research results for: {query}",
        f"Visited {len(sources)} page(s).",
    ]
    if quotes:
        lines.append("Key excerpts:")
        for quote in quotes[:6]:
            lines.append(f"- {quote}")
    else:
        lines.append(
            "No strong text excerpts were extracted, but pages "
            "were visited."
        )

    if artifacts:
        lines.append(f"Captured {len(artifacts)} downloaded artifact(s).")

    lines.append("Sources:")
    for source in sources:
        lines.append(f"- {source}")

    return "\n".join(lines)


def _build_blocked_answer(error: "BrowserAutomationBlockedError") -> str:
    payload = {
        "status": "automation_blocked",
        "last_url": error.last_url,
        "reason": error.reason,
        "tried": error.tried_actions,
    }
    return json.dumps(payload, ensure_ascii=False)
async def run_web_research(
    query: str,
    max_results: int = 5,
    max_pages: int = 8,
    max_steps: int = 40,
    download: bool = True,
    allowed_domains: list[str] | None = None,
    seed_urls: list[str] | None = None,
) -> dict[str, Any]:
    from .browse import BrowserAutomationBlockedError, browse_url

    seeded_urls = _dedupe_keep_order(
        [
            url
            for url in (
                *(seed_urls or []),
                *_extract_urls(query),
            )
            if isinstance(url, str) and url.strip()
        ]
    )
    if allowed_domains:
        seeded_urls = [
            url for url in seeded_urls
            if _url_allowed(url, allowed_domains)
        ]

    searched: list[dict[str, str]] = []
    if not seeded_urls:
        try:
            searched = await search_searxng(
                query=query,
                max_results=max_results,
            )
        except SearxSearchError as exc:
            return {
                "answer": f"SearxNG search failed: {exc}",
                "sources": [],
                "quotes": [],
                "artifacts": [],
                "trace": {"searched": [], "seeded": seeded_urls, "visited": [], "downloads": []},
            }

        if allowed_domains:
            searched = [
                item for item in searched
                if _url_allowed(
                    item.get("url", ""), allowed_domains
                )
            ]

    candidate_urls = _dedupe_keep_order(
        [
            url
            for url in (
                *seeded_urls,
                *(item.get("url", "") for item in searched),
            )
            if isinstance(url, str) and url.strip()
        ]
    )
    if allowed_domains:
        candidate_urls = [
            url for url in candidate_urls
            if _url_allowed(url, allowed_domains)
        ]
    if not candidate_urls:
        msg = "No results matched query/domain constraints for:"
        return {
            "answer": f"{msg} {query}",
            "sources": [],
            "quotes": [],
            "artifacts": [],
            "trace": {"searched": searched, "visited": [], "downloads": []},
        }

    visited: list[str] = []
    quotes: list[str] = []
    artifacts_by_path: dict[str, dict[str, Any]] = {}
    blocked_error: BrowserAutomationBlockedError | None = None
    profile = _query_profile(query)
    file_request = bool(profile.get("file_like"))
    repo_request = bool(profile.get("repo_like"))

    pages_budget = max_pages
    steps_budget = max_steps

    for index, url in enumerate(candidate_urls):
        if pages_budget <= 0 or steps_budget <= 0:
            break

        remaining_targets = max(1, len(candidate_urls) - index)
        min_pages = 2 if (file_request or repo_request) else 1
        min_steps = 8 if (file_request or repo_request) else 4
        pages_for_target = max(
            min_pages,
            pages_budget // remaining_targets,
        )
        pages_for_target = min(max(1, pages_budget), pages_for_target)
        steps_for_target = max(min_steps, steps_budget // remaining_targets)
        browse_timeout = max(30, min(120, steps_for_target * 5))
        if repo_request:
            browse_timeout = max(45, browse_timeout)

        try:
            result = await asyncio.wait_for(
                browse_url(
                    query=query,
                    start_url=url,
                    max_pages=pages_for_target,
                    max_steps=steps_for_target,
                    download=download,
                    allowed_domains=allowed_domains,
                ),
                timeout=browse_timeout,
            )
        except TimeoutError:
            logger.warning("Browsing timed out for %s", url)
            continue
        except BrowserAutomationBlockedError as exc:
            blocked_error = exc
            msg = "Automation block while browsing %s: %s"
            logger.warning(msg, url, exc)
            break
        except Exception as exc:
            msg = "Browsing failed for %s: %s"
            logger.exception(msg, url, exc)
            continue

        visited.extend(result.get("visited_urls", []))
        quotes.extend(result.get("quotes", []))
        for artifact in result.get("artifacts", []):
            path = str(artifact.get("path", "")).strip()
            if path:
                artifacts_by_path[path] = artifact

        visited_count = len(result.get("visited_urls", []))
        pages_budget = max(0, pages_budget - visited_count)
        steps_taken = int(result.get("steps_taken", 0))
        steps_budget = max(0, steps_budget - steps_taken)
        if file_request and artifacts_by_path:
            break

    visited = _dedupe_keep_order(visited)
    quotes = _dedupe_keep_order([
        quote for quote in quotes
        if isinstance(quote, str) and quote.strip()
    ])
    artifacts = list(artifacts_by_path.values())

    if blocked_error and not visited:
        answer = _build_blocked_answer(blocked_error)
    else:
        answer = _build_answer(
            query=query,
            sources=visited,
            quotes=quotes,
            artifacts=artifacts,
        )

    trace: dict[str, Any] = {
        "searched": searched,
        "seeded": candidate_urls,
        "visited": visited,
        "downloads": [
            artifact.get("path") for artifact in artifacts
            if artifact.get("path")
        ],
    }

    if blocked_error:
        trace["automation_block"] = {
            "last_url": blocked_error.last_url,
            "reason": blocked_error.reason,
            "tried": blocked_error.tried_actions,
        }
        if visited:
            blocked_msg = _build_blocked_answer(blocked_error)
            answer = (
                f"{answer}\n\nAutomation block encountered "
                f"later: {blocked_msg}"
            )

    return {
        "answer": answer,
        "sources": visited,
        "quotes": quotes,
        "artifacts": artifacts,
        "trace": trace,
    }
