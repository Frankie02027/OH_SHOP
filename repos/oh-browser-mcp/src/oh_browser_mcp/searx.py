from __future__ import annotations

import asyncio
import importlib
import re
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx

from .config import get_settings


class SearxSearchError(RuntimeError):
    pass


STOPWORDS = {
    "a",
    "all",
    "an",
    "and",
    "as",
    "at",
    "by",
    "can",
    "current",
    "do",
    "find",
    "for",
    "from",
    "get",
    "how",
    "i",
    "in",
    "is",
    "it",
    "its",
    "let",
    "me",
    "need",
    "of",
    "on",
    "one",
    "or",
    "our",
    "please",
    "show",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "up",
    "url",
    "use",
    "with",
    "you",
}

FILE_INTENT_TOKENS = {
    "archive",
    "asset",
    "attachment",
    "binary",
    "checksum",
    "download",
    "file",
    "package",
    "release",
    "sha256",
    "zip",
}

REPO_INTENT_TOKENS = {
    "asset",
    "binary",
    "code",
    "download",
    "github",
    "gitlab",
    "package",
    "project",
    "release",
    "repo",
    "repository",
    "source",
    "zip",
}

REPO_HOST_HINTS = (
    "github.com",
    "gitlab.com",
    "gitee.com",
    "raw.githubusercontent.com",
)

REPO_OWNER_NOISE_HINTS = (
    "archive",
    "backup",
    "fork",
    "mirror",
)

NOISE_HOST_HINTS = (
    "apple.com",
    "mercadolibre.com",
    "play.google.com",
    "stackoverflow.com",
    "zhidao.baidu.com",
)

SEARCH_ATTEMPT_DELAYS = (0.0, 1.5, 3.0, 4.5)

BROWSER_SEARCH_PROVIDERS = (
    {
        "name": "github_repo_search",
        "url": "https://github.com/search?q={query}&type=repositories",
        "host": "github.com",
        "mode": "github_repo_search",
    },
    {
        "name": "duckduckgo_html",
        "url": "https://html.duckduckgo.com/html/?q={query}",
        "host": "duckduckgo.com",
        "mode": "generic_search",
    },
)

BROWSER_SEARCH_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)

BROWSER_SEARCH_INIT_SCRIPT = """
(() => {
  try {
    Object.defineProperty(navigator, 'webdriver', {
      configurable: true,
      get: () => undefined,
    });
  } catch (err) {}
})();
"""

GITHUB_REPO_NAME_RE = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b")


def _tokenize_query(query: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]*", query or "")
    tokens: list[str] = []
    for token in raw_tokens:
        cleaned = token.strip("._-")
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _query_profile(query: str) -> dict[str, Any]:
    tokens = _tokenize_query(query)
    raw_tokens_lower = [token.lower() for token in tokens]
    meaningful_tokens = [
        token for token in tokens
        if token.lower() not in STOPWORDS
    ]
    intent_tokens = [
        token for token in meaningful_tokens
        if token.lower() in REPO_INTENT_TOKENS
    ]
    entity_tokens = [
        token for token in meaningful_tokens
        if token.lower() not in REPO_INTENT_TOKENS
    ]
    if not entity_tokens:
        entity_tokens = meaningful_tokens[:]

    repo_like = bool(
        intent_tokens
        or any(
            token in {"project", "repo", "repository", "source", "code"}
            for token in raw_tokens_lower
        )
    )
    file_like = bool(
        any(token in FILE_INTENT_TOKENS for token in raw_tokens_lower)
        or any("." in token for token in tokens)
    )

    return {
        "raw": " ".join(query.split()),
        "raw_tokens": tokens,
        "tokens": meaningful_tokens,
        "entity_tokens": _unique_keep_order(entity_tokens),
        "intent_tokens": _unique_keep_order(intent_tokens),
        "repo_like": repo_like,
        "file_like": file_like,
    }


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _playwright_async_api() -> Any:
    return importlib.import_module("playwright.async_api")


def best_search_query(query: str) -> str:
    profile = _query_profile(query)
    entity_tokens = profile["entity_tokens"]
    if entity_tokens:
        return " ".join(entity_tokens)
    return profile["raw"]


def _normalize_results(
    payload: dict[str, Any],
    max_results: int,
) -> list[dict[str, str]]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise SearxSearchError("SearxNG JSON payload missing 'results' list.")

    normalized: list[dict[str, str]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue

        url = str(item.get("url", "")).strip()
        if not url:
            continue

        normalized.append(
            {
                "title": str(item.get("title", "")).strip() or url,
                "url": url,
                "snippet": str(
                    item.get("content", "")
                    or item.get("snippet", "")
                ).strip(),
            }
        )

        if len(normalized) >= max_results:
            break

    return normalized


def _candidate_search_params(query: str) -> list[dict[str, str]]:
    profile = _query_profile(query)
    raw_query = profile["raw"] or query
    focused_query = best_search_query(query)
    intent_tokens = {token.lower() for token in profile["intent_tokens"]}
    default_params = {"q": raw_query, "format": "json"}
    params_list: list[dict[str, str]] = []

    params_list.append(default_params)

    if "github" in raw_query.lower():
        params_list.append(
            {
                "q": focused_query,
                "format": "json",
                "engines": "github,github code",
            }
        )
    elif "gitlab" in raw_query.lower():
        params_list.append(
            {
                "q": focused_query,
                "format": "json",
                "engines": "gitlab",
            }
        )
    elif profile["repo_like"]:
        if profile["file_like"]:
            params_list.append(
                {
                    "q": focused_query,
                    "format": "json",
                    "engines": "github,gitlab,github code",
                }
            )
        if {"zip", "download", "release", "asset", "package"} & intent_tokens:
            params_list.append(
                {
                    "q": f"{focused_query} zip".strip(),
                    "format": "json",
                    "engines": "github,gitlab,github code",
                }
            )
        params_list.append(
            {
                "q": f"{focused_query} official".strip(),
                "format": "json",
            }
        )
    params_list.append(
        {
            "q": focused_query,
            "format": "json",
            "engines": "mojeek,bing,wikipedia",
        }
    )

    unique: list[dict[str, str]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    for params in params_list:
        key = tuple(sorted(params.items()))
        if key in seen:
            continue
        seen.add(key)
        unique.append(params)
    return unique


def _score_result(
    result: dict[str, str],
    query: str,
) -> float:
    profile = _query_profile(query)
    entity_tokens = [token.lower() for token in profile["entity_tokens"]]
    entity_slugs = [_slugify(token) for token in profile["entity_tokens"]]
    entity_slugs = [slug for slug in entity_slugs if slug]
    intent_tokens = {token.lower() for token in profile["intent_tokens"]}
    repo_like = bool(profile["repo_like"])
    file_like = bool(profile["file_like"])

    title = result.get("title", "")
    url = result.get("url", "")
    snippet = result.get("snippet", "")
    engine = result.get("engine", "")

    haystack = f"{title} {snippet} {url}".lower()
    parsed_url = urlparse(url)
    host = (parsed_url.hostname or "").lower()
    path = parsed_url.path.lower()
    path_parts = [part for part in path.split("/") if part]
    owner = path_parts[0] if len(path_parts) >= 1 else ""
    repo_name = path_parts[1] if len(path_parts) >= 2 else ""
    owner_slug = _slugify(owner)
    repo_slug = _slugify(repo_name)

    score = 0.0
    engine_boosts = {
        "github": 1.5,
        "github code": 1.0,
        "gitlab": 1.0,
        "bing": 0.25,
        "mojeek": 0.25,
        "wikipedia": 0.25,
    }
    score += engine_boosts.get(engine.lower(), 0.0)

    host_slug = _slugify(host)
    host_labels = [label for label in host.split(".") if label]
    for slug in entity_slugs:
        if not slug:
            continue
        if slug and slug in host_slug:
            score += 5.0
        if any(_slugify(label) == slug for label in host_labels):
            score += 4.0

    matched_entity_terms = 0
    for term in entity_tokens:
        if term in haystack:
            matched_entity_terms += 1
            score += 3.0
        if path_parts and term == path_parts[-1]:
            score += 3.0
        elif path_parts and path_parts[-1].startswith(term):
            score += 2.5
        elif path_parts and term in path_parts[-1]:
            score += 2.0
        elif any(term == part for part in path_parts):
            score += 1.5
        if path_parts and term in path_parts[0]:
            score += 1.5
    if entity_tokens and matched_entity_terms == 0:
        score -= 8.0

    if repo_like and any(hint in host for hint in REPO_HOST_HINTS):
        score += 5.0
        if len(path_parts) == 1:
            score -= 6.0
        elif len(path_parts) == 2:
            score += 2.0
        elif "/blob/" in path or "/tree/" in path:
            score += 1.0
        if "/orgs/" in path or path.endswith("/repositories"):
            score -= 5.0
        if path_parts and path_parts[-1] in {"repositories", "projects"}:
            score -= 5.0
        if any(noise in owner_slug for noise in REPO_OWNER_NOISE_HINTS):
            score -= 2.5
        for slug in entity_slugs:
            if not slug:
                continue
            if repo_slug == slug:
                score += 3.0
                if owner_slug == slug or slug in owner_slug:
                    score += 3.0
                elif {"repo", "repository", "project"} & intent_tokens:
                    score -= 6.0
            elif owner_slug == slug:
                score += 4.0
            elif slug in owner_slug and repo_slug.startswith(slug):
                score += 6.0
            elif slug in owner_slug:
                score += 3.0
            elif repo_slug.startswith(slug):
                score += 1.5
            elif slug in repo_slug:
                score += 0.75
            if owner_slug == slug and repo_slug and repo_slug != slug:
                score += 3.5
            if repo_slug.endswith(slug) and repo_slug != slug:
                score += 0.5
        if (
            len(path_parts) == 2
            and entity_slugs
            and not any(owner_slug == slug for slug in entity_slugs)
            and not any(repo_slug == slug for slug in entity_slugs)
            and any(slug in owner_slug or slug in repo_slug for slug in entity_slugs)
        ):
            score -= 2.5
        if (
            len(path_parts) == 2
            and entity_slugs
            and repo_slug
            and not any(repo_slug == slug for slug in entity_slugs)
            and any(slug in repo_slug for slug in entity_slugs)
            and any(noise in owner_slug for noise in REPO_OWNER_NOISE_HINTS)
        ):
            score -= 2.0
    if repo_like and any(hint in host for hint in NOISE_HOST_HINTS):
        score -= 6.0
    if repo_like and {"repo", "repository", "project"} & intent_tokens:
        if any(hint in host for hint in REPO_HOST_HINTS):
            score += 2.0
        if "/search" in url:
            score += 1.0
        if "/blob/" in url or "/tree/" in url:
            score += 1.5
    if {"zip", "download", "release", "asset", "package"} & intent_tokens:
        if url.lower().split("?", 1)[0].endswith(
            (".zip", ".tar.gz", ".tgz", ".7z", ".tar", ".gz")
        ):
            score += 7.0
        if "/releases/" in path or "/archive/" in path:
            score += 3.0
    if file_like:
        if any(hint in host for hint in REPO_HOST_HINTS):
            if len(path_parts) == 2:
                score -= 5.0
            if "/blob/" in path or "/raw/" in path:
                score += 7.0
            elif "/releases/download/" in path or "/archive/" in path:
                score += 6.0
            elif len(path_parts) >= 4:
                score += 2.0
        if url.lower().split("?", 1)[0].endswith(
            (
                ".zip",
                ".tar.gz",
                ".tgz",
                ".7z",
                ".tar",
                ".gz",
                ".md",
                ".txt",
                ".pdf",
            )
        ):
            score += 5.0
        if any(hint in host for hint in NOISE_HOST_HINTS):
            score -= 4.0
        elif not any(hint in host for hint in REPO_HOST_HINTS):
            score -= 2.0

    return score


def _rank_results(
    query: str,
    results: list[dict[str, str]],
    max_results: int,
) -> list[dict[str, str]]:
    profile = _query_profile(query)
    repo_like = bool(profile["repo_like"])
    min_score = 2.5 if repo_like else 0.0

    ranked: list[tuple[float, dict[str, str]]] = []
    for result in results:
        score = _score_result(result, query)
        if score < min_score:
            continue
        ranked.append((score, result))

    ranked.sort(
        key=lambda item: (
            item[0],
            item[1].get("url", ""),
        ),
        reverse=True,
    )

    deduped: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for _, result in ranked:
        url = result.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(result)
        if len(deduped) >= max_results:
            break
    return deduped


async def _browser_search_results(
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    try:
        playwright_api = _playwright_async_api()
    except ModuleNotFoundError:
        return []

    async_playwright = getattr(playwright_api, "async_playwright", None)
    if async_playwright is None:
        return []

    collected: list[dict[str, str]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=BROWSER_SEARCH_USER_AGENT,
            locale="en-US",
            viewport={"width": 1440, "height": 900},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        await context.add_init_script(BROWSER_SEARCH_INIT_SCRIPT)
        page = await context.new_page()
        try:
            for provider in BROWSER_SEARCH_PROVIDERS:
                url = provider["url"].format(query=quote_plus(query))
                try:
                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=20000,
                    )
                    await asyncio.sleep(1.5)
                    if provider.get("mode") == "github_repo_search":
                        results = await page.evaluate(
                            """
                            ({ limit }) => {
                              const out = [];
                              const seen = new Set();
                              const skipOwners = new Set([
                                'search', 'login', 'signup', 'features',
                                'enterprise', 'pricing', 'topics', 'collections',
                                'marketplace', 'sponsors', 'orgs', 'explore',
                                'settings', 'site'
                              ]);
                              for (const a of document.querySelectorAll('a[href]')) {
                                if (out.length >= limit * 4) break;
                                let href = '';
                                try {
                                  href = new URL(a.getAttribute('href') || '', window.location.href).href;
                                } catch (err) {
                                  continue;
                                }
                                const parsed = new URL(href);
                                if (parsed.hostname !== 'github.com') continue;
                                const parts = parsed.pathname.split('/').filter(Boolean);
                                if (parts.length !== 2) continue;
                                if (skipOwners.has(parts[0])) continue;
                                const repoKey = parts.join('/').toLowerCase();
                                if (seen.has(repoKey)) continue;
                                seen.add(repoKey);
                                const container = a.closest('div, li, article');
                                const text = (
                                  a.innerText ||
                                  a.textContent ||
                                  repoKey
                                ).replace(/\\s+/g, ' ').trim();
                                if (!text.includes('/')) continue;
                                const snippet = ((container && container.innerText) || '')
                                  .replace(/\\s+/g, ' ')
                                  .trim();
                                out.push({ href, text, snippet });
                              }
                              return out;
                            }
                            """,
                            {"limit": max_results},
                        )
                    else:
                        results = await page.evaluate(
                            """
                            ({ host, limit }) => {
                              const out = [];
                              const sameHost = (href) => {
                                try {
                                  return new URL(href).hostname.includes(host);
                                } catch (err) {
                                  return true;
                                }
                              };
                              for (const a of document.querySelectorAll('a[href]')) {
                                if (out.length >= limit * 4) break;
                                const href = a.href || '';
                                const text = (a.innerText || a.textContent || '')
                                  .replace(/\\s+/g, ' ')
                                  .trim();
                                if (!href.startsWith('http')) continue;
                                if (!text || text.length < 8) continue;
                                if (sameHost(href)) continue;
                                const container = a.closest('article, .result, .w-gl__result, li, div');
                                const snippet = ((container && container.innerText) || '')
                                  .replace(/\\s+/g, ' ')
                                  .trim();
                                out.push({ href, text, snippet });
                              }
                              return out;
                            }
                            """,
                            {"host": provider["host"], "limit": max_results},
                        )
                except Exception:
                    results = []

                for item in results or []:
                    if not isinstance(item, dict):
                        continue
                    href = str(item.get("href", "")).strip()
                    if not href:
                        continue
                    collected.append(
                        {
                            "title": str(item.get("text", "")).strip() or href,
                            "url": href,
                            "snippet": str(item.get("snippet", "")).strip(),
                            "engine": provider["name"],
                        }
                    )

                if collected:
                    break
        finally:
            await context.close()
            await browser.close()
    return collected


async def _github_repo_search_results(
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    url = f"https://github.com/search?q={quote_plus(query)}&type=repositories"
    try:
        playwright_api = _playwright_async_api()
    except ModuleNotFoundError:
        return []
    async_playwright = getattr(playwright_api, "async_playwright", None)
    if async_playwright is None:
        return []
    profile = _query_profile(query)
    entity_slugs = {
        _slugify(token)
        for token in profile["entity_tokens"]
        if _slugify(token)
    }
    if not entity_slugs:
        fallback_slug = _slugify(query)
        if fallback_slug:
            entity_slugs = {fallback_slug}

    skip_owners = {
        "about",
        "collections",
        "enterprise",
        "events",
        "explore",
        "features",
        "github-copilot",
        "issues",
        "login",
        "marketplace",
        "orgs",
        "pricing",
        "pulls",
        "search",
        "settings",
        "site",
        "signup",
        "solutions",
        "sponsors",
        "topics",
    }
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=BROWSER_SEARCH_USER_AGENT,
                locale="en-US",
                viewport={"width": 1440, "height": 900},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )
            await context.add_init_script(BROWSER_SEARCH_INIT_SCRIPT)
            page = await context.new_page()
            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=20000,
                )
                await page.wait_for_timeout(1500)
                raw_results = await page.evaluate(
                    """
                    ({ limit }) => {
                      const out = [];
                      const seen = new Set();
                      const skipOwners = new Set([
                        'about', 'collections', 'enterprise', 'events',
                        'explore', 'features', 'github-copilot', 'issues',
                        'login', 'marketplace', 'orgs', 'pricing', 'pulls',
                        'search', 'settings', 'site', 'signup', 'solutions',
                        'sponsors', 'topics'
                      ]);
                      for (const a of document.querySelectorAll('a[href]')) {
                        if (out.length >= limit * 5) break;
                        let href = '';
                        try {
                          href = new URL(a.getAttribute('href') || '', window.location.href).href;
                        } catch (err) {
                          continue;
                        }
                        const parsed = new URL(href);
                        if (parsed.hostname !== 'github.com') continue;
                        const parts = parsed.pathname.split('/').filter(Boolean);
                        if (parts.length !== 2) continue;
                        if (skipOwners.has(parts[0])) continue;
                        const repoKey = parts.join('/');
                        const lowered = repoKey.toLowerCase();
                        if (seen.has(lowered)) continue;
                        seen.add(lowered);
                        const text = (
                          a.innerText ||
                          a.textContent ||
                          repoKey
                        ).replace(/\\s+/g, ' ').trim();
                        if (!text.includes('/')) continue;
                        const container = a.closest('div, li, article');
                        const snippet = ((container && container.innerText) || '')
                          .replace(/\\s+/g, ' ')
                          .trim();
                        out.push({ repoKey, href, text, snippet });
                      }
                      return out;
                    }
                    """,
                    {"limit": max_results},
                )
            finally:
                await context.close()
                await browser.close()
    except Exception:
        return []

    seen: set[str] = set()
    results: list[dict[str, str]] = []
    for item in raw_results or []:
        if not isinstance(item, dict):
            continue
        repo_key = str(item.get("repoKey", "")).strip()
        href = str(item.get("href", "")).strip()
        text = str(item.get("text", "")).strip()
        snippet = str(item.get("snippet", "")).strip()
        if not repo_key or not href:
            continue
        owner, repo = repo_key.split("/", 1)
        if owner.lower() in skip_owners:
            continue
        lowered = repo_key.lower()
        if lowered in seen:
            continue
        combined_slug = _slugify(f"{repo_key} {text} {snippet}")
        if entity_slugs and not any(slug in combined_slug for slug in entity_slugs):
            continue
        seen.add(lowered)
        results.append(
            {
                "title": text or repo_key,
                "url": href,
                "snippet": snippet or repo_key,
                "engine": "github_repo_search_text",
            }
        )
        if len(results) >= max_results * 3:
            break
    return results


async def _github_api_repo_search_results(
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    profile = _query_profile(query)
    focused_query = best_search_query(query) or query
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": focused_query, "per_page": max(1, min(max_results, 10))},
                headers={
                    "User-Agent": BROWSER_SEARCH_USER_AGENT,
                    "Accept": "application/vnd.github+json",
                },
            )
    except httpx.RequestError:
        return []
    if response.status_code != 200:
        return []
    try:
        payload = response.json()
    except ValueError:
        return []
    items = payload.get("items")
    if not isinstance(items, list):
        return []

    entity_slugs = {
        _slugify(token)
        for token in profile["entity_tokens"]
        if _slugify(token)
    }
    if not entity_slugs:
        fallback_slug = _slugify(query)
        if fallback_slug:
            entity_slugs = {fallback_slug}

    results: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        full_name = str(item.get("full_name", "")).strip()
        html_url = str(item.get("html_url", "")).strip()
        description = str(item.get("description", "") or "").strip()
        if not full_name or not html_url:
            continue
        combined_slug = _slugify(f"{full_name} {description}")
        if entity_slugs and not any(slug in combined_slug for slug in entity_slugs):
            continue
        results.append(
            {
                "title": full_name,
                "url": html_url,
                "snippet": description or full_name,
                "engine": "github_repo_search_api",
            }
        )
    return results


async def search_searxng(
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    if not query.strip():
        raise SearxSearchError("SearxNG query cannot be empty.")

    if max_results <= 0:
        return []

    settings = get_settings()
    endpoint = f"{settings.searxng_url}/search"

    last_error: str | None = None
    collected_results: list[dict[str, str]] = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt_index, params in enumerate(_candidate_search_params(query)):
                delay = SEARCH_ATTEMPT_DELAYS[
                    min(attempt_index, len(SEARCH_ATTEMPT_DELAYS) - 1)
                ]
                if delay > 0:
                    await asyncio.sleep(delay)
                try:
                    response = await client.get(endpoint, params=params)
                except httpx.RequestError as exc:
                    last_error = (
                        f"Failed to reach SearxNG at {endpoint}. "
                        "Verify that the searxng service is running and reachable."
                    )
                    raise SearxSearchError(last_error) from exc

                if response.status_code != 200:
                    last_error = (
                        "SearxNG returned HTTP "
                        f"{response.status_code} for query {query!r}: "
                        f"{response.text[:300]}"
                    )
                    continue

                try:
                    payload: dict[str, Any] = response.json()
                except ValueError as exc:
                    raise SearxSearchError("SearxNG returned invalid JSON.") from exc

                normalized = _normalize_results(payload, max_results)
                if normalized:
                    attempt_results: list[dict[str, str]] = []
                    for item in payload.get("results", []):
                        if not isinstance(item, dict):
                            continue
                        url = str(item.get("url", "")).strip()
                        if not url:
                            continue
                        attempt_results.append(
                            {
                                "title": str(item.get("title", "")).strip() or url,
                                "url": url,
                                "snippet": str(
                                    item.get("content", "")
                                    or item.get("snippet", "")
                                ).strip(),
                                "engine": str(item.get("engine", "")).strip(),
                            }
                        )
                    collected_results.extend(attempt_results)
    except SearxSearchError:
        raise

    ranked = _rank_results(query, collected_results, max_results)
    if ranked:
        return [
            {
                "title": item["title"],
                "url": item["url"],
                "snippet": item["snippet"],
            }
            for item in ranked
        ]

    profile = _query_profile(query)
    if profile["repo_like"]:
        github_api_results = await _github_api_repo_search_results(query, max_results)
        ranked_github_api = _rank_results(query, github_api_results, max_results)
        if ranked_github_api:
            return [
                {
                    "title": item["title"],
                    "url": item["url"],
                    "snippet": item["snippet"],
                }
                for item in ranked_github_api
            ]

        github_repo_results = await _github_repo_search_results(query, max_results)
        ranked_github_repo = _rank_results(query, github_repo_results, max_results)
        if ranked_github_repo:
            return [
                {
                    "title": item["title"],
                    "url": item["url"],
                    "snippet": item["snippet"],
                }
                for item in ranked_github_repo
            ]

    browser_results = await _browser_search_results(query, max_results)
    ranked_browser = _rank_results(query, browser_results, max_results)
    if ranked_browser:
        return [
            {
                "title": item["title"],
                "url": item["url"],
                "snippet": item["snippet"],
            }
            for item in ranked_browser
        ]

    if last_error:
        raise SearxSearchError(last_error)
    return []
