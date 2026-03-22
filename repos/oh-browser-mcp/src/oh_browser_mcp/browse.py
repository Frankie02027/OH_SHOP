from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import logging
import time
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import get_settings
from .downloads import artifact_record, ensure_download_dir
from .searx import _query_profile

logger = logging.getLogger(__name__)

BLOCK_MARKERS = (
    "captcha",
    "cloudflare",
    "attention required",
    "verify you are human",
    "access denied",
    "bot detected",
    "unusual traffic",
)

DOWNLOAD_EXTENSIONS = (
    ".pdf",
    ".csv",
    ".zip",
    ".xlsx",
    ".xls",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".json",
    ".xml",
    ".txt",
    ".md",
    ".tar",
    ".gz",
    ".7z",
)

NOISE_LINK_HINTS = (
    "login",
    "sign in",
    "sign-in",
    "signup",
    "register",
    "privacy",
    "terms",
    "cookie",
    "advertise",
    "feedback",
)

NOISE_PATH_HINTS = (
    "report-content",
    "/contact",
    "/login",
    "/signup",
    "/join",
    "/account",
    "/sessions",
)

PAGE_ROUTE_HINTS = (
    "/blob/",
    "/tree/",
    "/issues/",
    "/pull/",
    "/wiki/",
    "/commit/",
    "/commits/",
    "/compare/",
    "/search",
)

DIRECT_DOWNLOAD_ROUTE_HINTS = (
    "/download/",
    "/downloads/",
    "/releases/download/",
    "/archive/",
    "/raw/",
)

DOWNLOAD_TEXT_HINTS = (
    "download",
    "raw",
    "view raw",
    "plain text",
    "asset",
    "installer",
    "package",
    "binary",
    "release",
    "linux",
    "amd64",
    "x86_64",
    "arm64",
    ".deb",
    ".rpm",
    ".tar.gz",
    ".zip",
)

EXPAND_CONTROL_HINTS = (
    "show more",
    "show all",
    "more assets",
    "assets",
    "expand",
    "see more",
)

NAVIGATION_PAUSE_SECONDS = 1.2
INTERACTION_PAUSE_SECONDS = 0.8
HOST_REQUEST_INTERVAL_SECONDS = 2.5
PAGE_GOTO_TIMEOUT_MS = 10000
DOWNLOAD_WAIT_TIMEOUT_MS = 12000

REALISTIC_USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36",
)

REALISTIC_VIEWPORTS = (
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1600, "height": 900},
    {"width": 1920, "height": 1080},
)

STEALTH_INIT_SCRIPT = """
(() => {
  const define = (obj, key, value) => {
    try {
      Object.defineProperty(obj, key, {
        configurable: true,
        enumerable: true,
        get: () => value,
      });
    } catch (err) {}
  };

  define(navigator, 'webdriver', undefined);
  define(navigator, 'languages', ['en-US', 'en']);
  define(navigator, 'language', 'en-US');
  define(navigator, 'platform', 'Win32');
  define(navigator, 'hardwareConcurrency', 8);
  define(navigator, 'deviceMemory', 8);
  define(navigator, 'plugins', [
    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
    { name: 'Native Client', filename: 'internal-nacl-plugin' },
  ]);

  if (!window.chrome) {
    Object.defineProperty(window, 'chrome', {
      configurable: true,
      enumerable: true,
      value: { runtime: {}, app: {} },
    });
  }

  const originalQuery = navigator.permissions && navigator.permissions.query;
  if (originalQuery) {
    navigator.permissions.query = (parameters) => (
      parameters && parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters)
    );
  }
})();
"""


@lru_cache(maxsize=1)
def _chat_openai_cls() -> Any:
    try:
        module = importlib.import_module("langchain_openai")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: langchain-openai. "
            "Install dependencies for this project."
        ) from exc

    chat_cls = getattr(module, "ChatOpenAI", None)
    if chat_cls is None:
        raise RuntimeError("langchain_openai.ChatOpenAI is not available.")
    return chat_cls


@lru_cache(maxsize=1)
def _playwright_async_api() -> Any:
    try:
        return importlib.import_module("playwright.async_api")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: playwright. "
            "Install dependencies for this project."
        ) from exc


@dataclass
class BrowserAutomationBlockedError(RuntimeError):
    last_url: str
    reason: str
    tried_actions: list[str]

    def __str__(self) -> str:
        return f"Automation blocked at {self.last_url}: {self.reason}"


def _clip(text: str, max_len: int = 280) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 3] + "..."


def _normalize_allowed_domains(
    allowed_domains: list[str] | None,
) -> set[str] | None:
    if not allowed_domains:
        return None

    normalized: set[str] = set()
    for domain in allowed_domains:
        cleaned = domain.strip().lower()
        if not cleaned:
            continue
        if "://" in cleaned:
            cleaned = urlparse(cleaned).hostname or cleaned
        cleaned = cleaned.lstrip(".")
        if cleaned:
            normalized.add(cleaned)
    return normalized or None


def _host_allowed(url: str, allowed_domains: set[str] | None) -> bool:
    if not allowed_domains:
        return True
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    return any(
        host == domain or host.endswith(f".{domain}")
        for domain in allowed_domains
    )


def _is_downloadable_url(url: str) -> bool:
    parsed = urlparse(url)
    lower = url.lower().split("?", 1)[0]
    path = (parsed.path or "").lower()
    if not lower.endswith(DOWNLOAD_EXTENSIONS):
        return False
    if any(hint in path for hint in PAGE_ROUTE_HINTS):
        return False
    return True


def _is_noise_url(url: str) -> bool:
    parsed = urlparse(url)
    path = (parsed.path or "").lower()
    return any(hint in path for hint in NOISE_PATH_HINTS)


def _url_path_depth(url: str) -> int:
    path = urlparse(url).path
    if not path:
        return 0
    return len([part for part in path.split("/") if part])


def _host_family(host: str) -> str:
    parts = [part for part in (host or "").lower().split(".") if part]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return (host or "").lower()


def _path_segments(url: str) -> list[str]:
    path = (urlparse(url).path or "").strip("/")
    if not path:
        return []
    return [part.lower() for part in path.split("/") if part]


def _shared_path_prefix_depth(left: str, right: str) -> int:
    depth = 0
    for left_part, right_part in zip(_path_segments(left), _path_segments(right)):
        if left_part != right_part:
            break
        depth += 1
    return depth


def _score_link(
    link: dict[str, str],
    query_terms: set[str],
    current_url: str,
    prefer_download: bool,
    file_like: bool,
) -> float:
    href = link.get("href", "")
    text = link.get("text", "")
    text_lower = f"{text} {href}".lower()
    current_host = (urlparse(current_url).hostname or "").lower()
    href_host = (urlparse(href).hostname or "").lower()
    href_segments = _path_segments(href)
    last_segment = href_segments[-1] if href_segments else ""

    if _is_noise_url(href):
        return -100.0

    score = 0.0
    for term in query_terms:
        if term in text_lower:
            score += 3.0

    if current_host and href_host == current_host:
        score += 3.0
    elif current_host and href_host:
        if _host_family(href_host) == _host_family(current_host):
            score += 0.5
        else:
            score -= 2.0

    shared_prefix_depth = _shared_path_prefix_depth(current_url, href)
    score += min(shared_prefix_depth, 4) * 1.25
    if current_host and href_host == current_host and shared_prefix_depth == 0:
        score -= 1.0

    score -= _url_path_depth(href) * 0.1

    if any(noise in text_lower for noise in NOISE_LINK_HINTS):
        score -= 4.0

    if _is_downloadable_url(href):
        score += 3.0 if prefer_download else 1.0

    if "download" in text_lower:
        score += 2.0

    if file_like:
        href_lower = href.lower()
        if any(hint in href_lower for hint in DIRECT_DOWNLOAD_ROUTE_HINTS):
            score += 5.0
        elif any(hint in href_lower for hint in PAGE_ROUTE_HINTS):
            score += 2.0
        if "." in last_segment:
            score += 4.0
        if last_segment and any(term in last_segment for term in query_terms):
            score += 2.5

    if not prefer_download and not any(term in text_lower for term in query_terms):
        if current_host and href_host and href_host != current_host:
            score -= 3.0

    return score


def _looks_downloadish_link(
    link: dict[str, str],
    query_terms: set[str],
) -> bool:
    href = str(link.get("href", "")).strip()
    text = str(link.get("text", "")).strip()
    text_lower = text.lower()
    href_lower = href.lower()

    if _is_noise_url(href):
        return False

    if _is_downloadable_url(href):
        return True

    if any(hint in href_lower for hint in PAGE_ROUTE_HINTS):
        return False

    if any(hint in href_lower for hint in DIRECT_DOWNLOAD_ROUTE_HINTS):
        return True

    if any(hint in text_lower for hint in ("download", "downloads", "asset", "installer", "raw", "plain text")):
        return True
    return False


def _extract_query_terms(query: str) -> set[str]:
    profile = _query_profile(query)
    terms = {
        token.lower()
        for token in (
            profile["entity_tokens"] + profile["intent_tokens"]
        )
        if isinstance(token, str) and len(token.strip()) >= 3
    }
    if not terms:
        terms.add(query.strip().lower())
    return {term for term in terms if term}


async def _extract_snippets(
    page: Any,
    query_terms: set[str],
    limit: int = 4,
) -> list[str]:
    try:
        blocks = await page.evaluate(
            """
            () => {
              const selectors = "h1,h2,h3,p,li,article,section";
              const out = [];
              for (const el of document.querySelectorAll(selectors)) {
                const text = (el.innerText || "").replace(/\\s+/g, " ").trim();
                if (text.length >= 30) out.push(text);
                if (out.length >= 250) break;
              }
              return out;
            }
            """
        )
    except Exception:
        blocks = []

    snippets: list[str] = []
    if isinstance(blocks, list):
        scored: list[tuple[float, str]] = []
        for block in blocks:
            if not isinstance(block, str):
                continue
            lower = block.lower()
            score = sum(1 for term in query_terms if term in lower)
            if score > 0:
                scored.append((float(score), _clip(block)))
        scored.sort(key=lambda item: item[0], reverse=True)
        snippets.extend(text for _, text in scored[:limit])

    if snippets:
        return snippets

    # fallback if no query-matching blocks were found
    for block in (blocks or [])[:limit]:
        if isinstance(block, str):
            snippets.append(_clip(block))
    return snippets[:limit]


async def _extract_links(page: Any) -> list[dict[str, str]]:
    try:
        links = await page.evaluate(
            """
            () => {
              const out = [];
              for (const a of document.querySelectorAll("a[href]")) {
                const hrefAttr = a.getAttribute("href");
                if (!hrefAttr) continue;
                                if (
                                    hrefAttr.startsWith("javascript:") ||
                                    hrefAttr.startsWith("#")
                                ) continue;
                let href;
                try {
                  href = new URL(hrefAttr, window.location.href).href;
                } catch (err) {
                  continue;
                }
                                if (
                                    !href.startsWith("http://") &&
                                    !href.startsWith("https://")
                                ) continue;
                                const text = (
                                    a.innerText ||
                                    a.getAttribute("title") ||
                                    ""
                                ).replace(/\\s+/g, " ").trim();
                out.push({ href, text });
                if (out.length >= 300) break;
              }
              return out;
            }
            """
        )
    except Exception:
        return []

    normalized: list[dict[str, str]] = []
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            href = str(link.get("href", "")).strip()
            if not href:
                continue
            normalized.append(
                {
                    "href": href,
                    "text": str(link.get("text", "")).strip(),
                }
            )
    return normalized


async def _expand_relevant_controls(page: Any) -> int:
    try:
        clicked = await page.evaluate(
            """
            (hints) => {
              const loweredHints = hints.map(h => h.toLowerCase());
              const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style &&
                  style.visibility !== 'hidden' &&
                  style.display !== 'none' &&
                  rect.width > 0 &&
                  rect.height > 0;
              };

              let count = 0;
              const seen = new Set();
              const selectors = 'button, summary, [role="button"], details summary';
              for (const el of document.querySelectorAll(selectors)) {
                if (count >= 5) break;
                if (!isVisible(el)) continue;
                const text = (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                if (!text) continue;
                if (!loweredHints.some(h => text.includes(h))) continue;
                if (seen.has(text)) continue;
                try {
                  el.click();
                  seen.add(text);
                  count += 1;
                } catch (err) {
                }
              }
              return count;
            }
            """,
            list(EXPAND_CONTROL_HINTS),
        )
    except Exception:
        return 0

    return int(clicked) if isinstance(clicked, int) else 0


async def _detect_automation_block(page: Any) -> str | None:
    title = ""
    body = ""
    try:
        title = (await page.title()).lower()
    except Exception:
        title = ""
    try:
        body = (
            await page.evaluate(
                "() => (document.body ? document.body.innerText : '')"
                ".slice(0, 25000).toLowerCase()"
            )
            or ""
        )
    except Exception:
        body = ""

    haystack = f"{title}\n{body}"
    for marker in BLOCK_MARKERS:
        if marker in haystack:
            return marker
    return None


def _result_to_text(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, str):
        return result

    for attr in ("final_result", "result", "summary", "message"):
        value = getattr(result, attr, None)
        if isinstance(value, str) and value.strip():
            return value

    if hasattr(result, "model_dump_json"):
        try:
            return result.model_dump_json(indent=2)
        except Exception:
            pass

    try:
        return json.dumps(result, default=str)
    except Exception:
        return str(result)


def _browser_use_supported(base_url: str, model: str) -> bool:
    normalized_base = (base_url or "").lower()
    normalized_model = (model or "").lower()
    if "host.docker.internal:1234" in normalized_base:
        return False
    if normalized_base.startswith("http://127.0.0.1:1234"):
        return False
    if normalized_base.startswith("http://localhost:1234"):
        return False
    if "openhands-lm" in normalized_model:
        return False
    return True


def _looks_like_browser_use_provider_error(text: str) -> bool:
    normalized = text.lower()
    markers = (
        "invalid tool_choice type",
        "supported string values: none, auto, required",
        "error code: 400",
        '"screenshot": "',
    )
    return any(marker in normalized for marker in markers)


def _safe_filename(name: str) -> str:
    clean = "".join(
        ch for ch in name if ch.isalnum() or ch in ("-", "_", ".", " ")
    )
    clean = clean.strip().replace(" ", "_")
    return clean or "download.bin"


def _looks_like_html_payload(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:512].lstrip()
    except OSError:
        return False
    lowered = sample.lower()
    return lowered.startswith(b"<!doctype html") or lowered.startswith(b"<html")


def _unique_path(download_dir: Path, filename: str) -> Path:
    candidate = download_dir / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    index = 1
    while True:
        next_candidate = download_dir / f"{stem}_{index}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        index += 1


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    candidate = Path(parsed.path).name
    return _safe_filename(candidate or "download.bin")


def _browser_profile(seed: str) -> dict[str, Any]:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    ua = REALISTIC_USER_AGENTS[digest[0] % len(REALISTIC_USER_AGENTS)]
    viewport = REALISTIC_VIEWPORTS[digest[1] % len(REALISTIC_VIEWPORTS)]
    return {
        "user_agent": ua,
        "viewport": viewport,
        "locale": "en-US",
        "timezone_id": "America/Chicago",
        "extra_headers": {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        },
    }


async def _paced_sleep(seconds: float) -> None:
    if seconds <= 0:
        return
    await asyncio.sleep(seconds)


async def _human_scroll(page: Any) -> None:
    try:
        for _ in range(2):
            distance = 250
            await page.mouse.wheel(0, distance)
            await asyncio.sleep(0.6)
        await page.mouse.wheel(0, -120)
        await asyncio.sleep(0.4)
    except Exception:
        return


async def _respect_host_backoff(
    url: str,
    last_request_at: dict[str, float],
) -> None:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return
    now = time.monotonic()
    previous = last_request_at.get(host)
    if previous is not None:
        wait_for = HOST_REQUEST_INTERVAL_SECONDS - (now - previous)
        if wait_for > 0:
            await asyncio.sleep(wait_for)
    last_request_at[host] = time.monotonic()


async def _save_download(download: Any, download_dir: Path) -> Path:
    suggested = _safe_filename(download.suggested_filename or "download.bin")
    target = _unique_path(download_dir, suggested)
    await download.save_as(str(target))
    if _looks_like_html_payload(target):
        try:
            target.unlink()
        except OSError:
            pass
        raise ValueError("download payload was HTML, not a real file")
    return target


async def _attempt_download(
    page: Any,
    href: str,
    download_dir: Path,
    last_request_at: dict[str, float],
) -> Path | None:
    playwright_api = _playwright_async_api()
    timeout_error = getattr(playwright_api, "TimeoutError", TimeoutError)
    download_name = _filename_from_url(href)

    # Strategy 1: click an existing anchor on the page if present.
    try:
        locator = page.locator(f'a[href="{href}"]').first
        if await locator.count() > 0:
            await _respect_host_backoff(href, last_request_at)
            await _paced_sleep(INTERACTION_PAUSE_SECONDS)
            async with page.expect_download(timeout=DOWNLOAD_WAIT_TIMEOUT_MS) as download_info:
                await locator.click()
            download = await download_info.value
            return await _save_download(download, download_dir)
    except Exception:
        pass

    # Strategy 2: synthetic anchor click.
    try:
        await _respect_host_backoff(href, last_request_at)
        await _paced_sleep(INTERACTION_PAUSE_SECONDS)
        async with page.expect_download(timeout=DOWNLOAD_WAIT_TIMEOUT_MS) as download_info:
            await page.evaluate(
                """
                ({ url, filename }) => {
                  const a = document.createElement("a");
                  a.href = url;
                  a.target = "_blank";
                  a.download = filename;
                  a.rel = "noopener noreferrer";
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                }
                """,
                {"url": href, "filename": download_name},
            )
        download = await download_info.value
        return await _save_download(download, download_dir)
    except timeout_error:
        pass
    except Exception:
        pass

    # Strategy 3: direct navigation to link.
    try:
        await _respect_host_backoff(href, last_request_at)
        await _paced_sleep(NAVIGATION_PAUSE_SECONDS)
        async with page.expect_download(timeout=DOWNLOAD_WAIT_TIMEOUT_MS) as download_info:
            await page.goto(
                href,
                wait_until="domcontentloaded",
                timeout=PAGE_GOTO_TIMEOUT_MS,
            )
        download = await download_info.value
        return await _save_download(download, download_dir)
    except Exception:
        pass

    return None


async def _run_browser_use_agent(
    query: str,
    start_url: str,
    max_pages: int,
    max_steps: int,
) -> list[str]:
    settings = get_settings()
    agent_browser: Any | None = None
    try:
        if not _browser_use_supported(settings.llm_base_url, settings.llm_model):
            logger.info(
                "Skipping browser-use agent for incompatible LM route/model "
                "(base_url=%s, model=%s)",
                settings.llm_base_url,
                settings.llm_model,
            )
            return []

        module = importlib.import_module("browser_use")
        agent_cls = getattr(module, "Agent", None)
        if agent_cls is None:
            return []

        chat_openai_cls = _chat_openai_cls()
        llm = chat_openai_cls(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=0.0,
        )

        task = (
            f"Research this query: {query}\n"
            f"Start at: {start_url}\n"
            "Follow links across multiple pages "
            f"(max_pages={max_pages}, max_steps={max_steps}).\n"
            "Return concise bullet findings with URL mentions."
        )

        browser_cls = getattr(module, "Browser", None)
        browser_config_cls = getattr(module, "BrowserConfig", None)
        if browser_cls is not None and browser_config_cls is not None:
            try:
                agent_browser = browser_cls(
                    config=browser_config_cls(headless=True)
                )
            except Exception as exc:
                logger.info(
                    "browser-use Browser() init failed for %s (%s)",
                    start_url,
                    exc,
                )
                agent_browser = None

        agent_kwargs: dict[str, Any] = {"task": task, "llm": llm}
        if agent_browser is not None:
            agent_kwargs["browser"] = agent_browser

        try:
            agent = agent_cls(generate_gif=False, **agent_kwargs)
        except TypeError:
            agent = agent_cls(**agent_kwargs)

        async def _run() -> Any:
            try:
                return await agent.run(max_steps=min(max_steps, 20))
            except TypeError:
                return await agent.run()

        raw = await asyncio.wait_for(
            _run(), timeout=max(40, min(180, max_steps * 4))
        )
        text = _result_to_text(raw)
        if _looks_like_browser_use_provider_error(text):
            logger.info(
                "Skipping browser-use agent notes because the provider "
                "returned an incompatible tool-calling payload."
            )
            return []
        notes: list[str] = []
        for line in text.splitlines():
            cleaned = line.strip().lstrip("- ").strip()
            if len(cleaned) < 25:
                continue
            notes.append(_clip(cleaned))
            if len(notes) >= 4:
                break
        return notes
    except Exception as exc:
        logger.info(
            "browser-use agent run skipped/fallback for %s (%s)",
            start_url,
            exc,
        )
        return []
    finally:
        if agent_browser is not None:
            try:
                await agent_browser.close()
            except Exception:
                pass


async def browse_url(
    query: str,
    start_url: str,
    max_pages: int,
    max_steps: int,
    download: bool = True,
    allowed_domains: list[str] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    download_dir = ensure_download_dir(settings.download_dir)
    allowed = _normalize_allowed_domains(allowed_domains)
    query_terms = _extract_query_terms(query)
    query_profile = _query_profile(query)
    file_like = bool(query_profile["file_like"])

    visited_urls: list[str] = []
    quotes: list[str] = []
    download_paths: list[Path] = []
    tried_actions: list[str] = []
    queue: deque[str] = deque([start_url])
    seen_enqueued: set[str] = {start_url}
    steps_taken = 0
    last_request_at: dict[str, float] = {}

    # Try browser-use first for agent-style navigation notes.
    agent_notes = await _run_browser_use_agent(
        query,
        start_url,
        max_pages=max_pages,
        max_steps=max_steps,
    )
    for note in agent_notes:
        if note not in quotes:
            quotes.append(note)

    playwright_api = _playwright_async_api()
    async_playwright = getattr(playwright_api, "async_playwright", None)
    if async_playwright is None:
        raise RuntimeError(
            "playwright.async_api.async_playwright is unavailable."
        )

    profile = _browser_profile(f"{query}\n{start_url}")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=download,
            user_agent=profile["user_agent"],
            viewport=profile["viewport"],
            locale=profile["locale"],
            timezone_id=profile["timezone_id"],
            extra_http_headers=profile["extra_headers"],
        )
        await context.add_init_script(STEALTH_INIT_SCRIPT)
        async def _route_handler(route: Any) -> None:
            if route.request.resource_type in {"image", "font", "media"}:
                await route.abort()
                return
            await route.continue_()

        await context.route("**/*", _route_handler)
        page = await context.new_page()

        try:
            while (
                queue
                and len(visited_urls) < max_pages
                and steps_taken < max_steps
            ):
                target_url = queue.popleft()
                if not _host_allowed(target_url, allowed):
                    continue

                if download and _is_downloadable_url(target_url):
                    tried_actions.append(f"download_start:{target_url}")
                    saved_path = await _attempt_download(
                        page,
                        target_url,
                        download_dir,
                        last_request_at,
                    )
                    steps_taken += 1
                    if saved_path is not None:
                        download_paths.append(saved_path)
                        if target_url not in visited_urls:
                            visited_urls.append(target_url)
                    continue

                tried_actions.append(f"goto:{target_url}")
                try:
                    await _respect_host_backoff(target_url, last_request_at)
                    await _paced_sleep(NAVIGATION_PAUSE_SECONDS)
                    await page.goto(
                        target_url,
                        wait_until="domcontentloaded",
                        timeout=PAGE_GOTO_TIMEOUT_MS,
                    )
                except Exception as exc:
                    logger.info(
                        "Navigation failed for %s: %s", target_url, exc
                    )
                    steps_taken += 1
                    continue

                steps_taken += 1
                current_url = page.url or target_url
                if current_url not in visited_urls:
                    visited_urls.append(current_url)

                await _paced_sleep(0.5)
                await _human_scroll(page)

                blocked_reason = await _detect_automation_block(page)
                if blocked_reason:
                    raise BrowserAutomationBlockedError(
                        last_url=current_url,
                        reason=blocked_reason,
                        tried_actions=tried_actions[-15:],
                    )

                expand_count = await _expand_relevant_controls(page)
                if expand_count:
                    tried_actions.append(f"expand_controls:{expand_count}")
                    await _paced_sleep(INTERACTION_PAUSE_SECONDS)
                    await page.wait_for_timeout(750)

                for snippet in await _extract_snippets(page, query_terms):
                    if snippet not in quotes:
                        quotes.append(snippet)
                    if len(quotes) >= 30:
                        break

                current_url_lower = current_url.lower()
                file_page_candidate = file_like and (
                    any(term in current_url_lower for term in query_terms)
                    and any(hint in current_url_lower for hint in PAGE_ROUTE_HINTS)
                )

                raw_links = await _extract_links(page)
                if not raw_links:
                    continue

                current_host = (urlparse(current_url).hostname or "").lower()
                download_links: list[dict[str, str]] = []
                nav_links: list[dict[str, str]] = []
                for link in raw_links:
                    href = link.get("href", "")
                    if not href or not _host_allowed(href, allowed):
                        continue
                    if _is_noise_url(href):
                        continue
                    href_host = (urlparse(href).hostname or "").lower()
                    combined_lower = (
                        f"{link.get('text', '')} {href}"
                    ).lower()
                    if (
                        file_like
                        and current_host
                        and href_host
                        and _host_family(href_host) != _host_family(current_host)
                        and not any(term in combined_lower for term in query_terms)
                        and not _looks_downloadish_link(link, query_terms)
                    ):
                        continue
                    if _looks_downloadish_link(link, query_terms):
                        download_links.append(link)
                    else:
                        nav_links.append(link)

                nav_links.sort(
                        key=lambda link: _score_link(
                            link,
                            query_terms,
                            current_url,
                            prefer_download=False,
                            file_like=file_like,
                        ),
                    reverse=True,
                )
                nav_cap = 0 if file_page_candidate else (1 if file_like else 3)
                for link in nav_links[:nav_cap]:
                    href = link["href"]
                    if href in seen_enqueued or href in visited_urls:
                        continue
                    seen_enqueued.add(href)
                    queue.append(href)

                if download and steps_taken < max_steps:
                    download_links.sort(
                        key=lambda link: _score_link(
                            link,
                            query_terms,
                            current_url,
                            prefer_download=True,
                            file_like=file_like,
                        ),
                        reverse=True,
                    )
                    for link in download_links[:2]:
                        if steps_taken >= max_steps:
                            break
                        href = link["href"]
                        tried_actions.append(f"download:{href}")
                        saved_path = await _attempt_download(
                            page,
                            href,
                            download_dir,
                            last_request_at,
                        )
                        steps_taken += 1
                        if saved_path is not None:
                            download_paths.append(saved_path)
                            continue

                        if href not in seen_enqueued and href not in visited_urls:
                            seen_enqueued.add(href)
                            queue.appendleft(href)

                if file_page_candidate:
                    queue.clear()
        finally:
            await context.close()
            await browser.close()

    # Remove duplicate paths while keeping order.
    unique_paths: list[Path] = []
    seen_paths: set[str] = set()
    for path in download_paths:
        key = str(path)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        unique_paths.append(path)

    artifacts = [
        artifact_record(path)
        for path in unique_paths
        if path.exists()
    ]

    return {
        "visited_urls": visited_urls,
        "quotes": quotes[:30],
        "artifacts": artifacts,
        "steps_taken": steps_taken,
        "tried_actions": tried_actions[-20:],
    }
