#!/usr/bin/env python3
"""Conservative OpenHands chat-state guard.

Purpose:
- Preserve conversation history by default.
- Remove only stale transient rows that no longer map to real conversations.
- Optionally run continuously in watch mode.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "openhands" / "openhands.db"
DEFAULT_OPENHANDS_URL = os.getenv("CHAT_GUARD_OPENHANDS_URL",
                                  "http://openhands:3000")
DEFAULT_SANDBOX_STALE_SECONDS = int(
    os.getenv("CHAT_GUARD_SANDBOX_STALE_SECONDS", "900"))


def _canon(conversation_id: str | None) -> str:
    if not conversation_id:
        return ""
    return conversation_id.replace("-", "").lower()


@dataclass
class CleanupStats:
    orphan_start_tasks: int = 0
    orphan_callbacks: int = 0
    orphan_callback_results: int = 0
    sandbox_containers_removed: int = 0
    sandbox_cleanup_skipped: str = ""


def _metadata_ids(cur: sqlite3.Cursor) -> set[str]:
    rows = cur.execute(
        "SELECT conversation_id FROM conversation_metadata").fetchall()
    return {_canon(row[0]) for row in rows}


def _delete_orphan_start_tasks(cur: sqlite3.Cursor,
                               valid_ids: set[str]) -> int:
    rows = cur.execute(
        "SELECT id, app_conversation_id FROM app_conversation_start_task"
    ).fetchall()
    orphan_ids = [
        row_id for row_id, app_conversation_id in rows
        if _canon(app_conversation_id) not in valid_ids
    ]
    if not orphan_ids:
        return 0
    placeholders = ",".join("?" for _ in orphan_ids)
    cur.execute(
        f"DELETE FROM app_conversation_start_task WHERE id IN ({placeholders})",
        orphan_ids,
    )
    return len(orphan_ids)


def _delete_orphan_callbacks(cur: sqlite3.Cursor,
                             valid_ids: set[str]) -> tuple[int, int]:
    rows = cur.execute(
        "SELECT id, conversation_id FROM event_callback").fetchall()
    orphan_callback_ids = [
        callback_id for callback_id, conversation_id in rows
        if _canon(conversation_id) not in valid_ids
    ]

    deleted_results = 0
    if orphan_callback_ids:
        placeholders = ",".join("?" for _ in orphan_callback_ids)
        result_rows = cur.execute(
            f"SELECT id FROM event_callback_result WHERE event_callback_id IN ({placeholders})",
            orphan_callback_ids,
        ).fetchall()
        result_ids = [row[0] for row in result_rows]
        if result_ids:
            result_placeholders = ",".join("?" for _ in result_ids)
            cur.execute(
                f"DELETE FROM event_callback_result WHERE id IN ({result_placeholders})",
                result_ids,
            )
            deleted_results = len(result_ids)

        cur.execute(
            f"DELETE FROM event_callback WHERE id IN ({placeholders})",
            orphan_callback_ids,
        )

    return len(orphan_callback_ids), deleted_results


def _delete_orphan_results_by_conversation(cur: sqlite3.Cursor,
                                           valid_ids: set[str]) -> int:
    rows = cur.execute(
        "SELECT id, conversation_id FROM event_callback_result").fetchall()
    orphan_result_ids = [
        result_id for result_id, conversation_id in rows
        if _canon(conversation_id) not in valid_ids
    ]
    if not orphan_result_ids:
        return 0
    placeholders = ",".join("?" for _ in orphan_result_ids)
    cur.execute(
        f"DELETE FROM event_callback_result WHERE id IN ({placeholders})",
        orphan_result_ids,
    )
    return len(orphan_result_ids)


def _http_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
) -> dict | list | None:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
        return None


def _created_at_ts(container: object) -> float:
    created = (getattr(container, "attrs", {}).get("Created",
                                                   "").replace("Z", "+00:00"))
    try:
        return datetime.fromisoformat(created).timestamp()
    except ValueError:
        return 0.0


def _cleanup_finished_sandboxes(
    *,
    openhands_url: str,
    stale_seconds: int,
) -> tuple[int, str]:
    try:
        import docker  # type: ignore
    except ImportError:
        return 0, "docker SDK unavailable"

    payload = _http_json(
        f"{openhands_url.rstrip('/')}/api/v1/app-conversations/search?limit=100"
    )
    if not isinstance(payload, dict):
        return 0, "app conversation search unavailable"

    items = payload.get("items")
    if not isinstance(items, list):
        return 0, "app conversation search returned no items"

    active_by_sandbox: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        sandbox_id = str(item.get("sandbox_id") or "").strip()
        if sandbox_id:
            active_by_sandbox[sandbox_id] = item

    client = docker.from_env()
    now = time.time()
    removed = 0

    for container in client.containers.list(
            all=True, filters={"name": "oh-agent-server-"}):
        name = str(getattr(container, "name", "") or "").strip()
        if not name.startswith("oh-agent-server-"):
            continue

        record = active_by_sandbox.get(name)
        execution_status = str((record or {}).get("execution_status")
                               or "").lower()
        sandbox_status = str((record or {}).get("sandbox_status")
                             or "").lower()
        age_seconds = max(0.0, now - _created_at_ts(container))
        container_status = str(getattr(container, "status", "") or "").lower()

        should_remove = False
        if execution_status in {"finished", "error", "failed", "stopped"}:
            should_remove = True
        elif sandbox_status in {"stopped", "terminated", "deleted"}:
            should_remove = True
        elif not record and age_seconds >= stale_seconds:
            should_remove = True
        elif container_status == "paused" and age_seconds >= stale_seconds:
            should_remove = True

        if not should_remove:
            continue

        container.remove(force=True)
        removed += 1

    return removed, ""


def run_once(
    db_path: Path,
    preserve_all_conversations: bool = True,
    *,
    openhands_url: str = DEFAULT_OPENHANDS_URL,
    sandbox_stale_seconds: int = DEFAULT_SANDBOX_STALE_SECONDS,
) -> CleanupStats:
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        valid_ids = _metadata_ids(cur)

        stats = CleanupStats()

        stats.orphan_start_tasks = _delete_orphan_start_tasks(cur, valid_ids)

        callbacks_deleted, callback_results_deleted_via_callback = _delete_orphan_callbacks(
            cur, valid_ids)
        stats.orphan_callbacks = callbacks_deleted
        stats.orphan_callback_results = callback_results_deleted_via_callback

        # Safety net for result rows that point to unknown conversations.
        stats.orphan_callback_results += _delete_orphan_results_by_conversation(
            cur, valid_ids)

        (
            stats.sandbox_containers_removed,
            stats.sandbox_cleanup_skipped,
        ) = _cleanup_finished_sandboxes(
            openhands_url=openhands_url,
            stale_seconds=sandbox_stale_seconds,
        )

        if not preserve_all_conversations:
            # Intentionally disabled by default. Keeping conversation history is the safe behavior.
            pass

        con.commit()
        return stats
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenHands stale-chat guard")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Path to OpenHands sqlite db (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Seconds between watch cycles (default: 60)",
    )
    parser.add_argument(
        "--openhands-url",
        default=DEFAULT_OPENHANDS_URL,
        help=f"OpenHands base URL (default: {DEFAULT_OPENHANDS_URL})",
    )
    parser.add_argument(
        "--sandbox-stale-seconds",
        type=int,
        default=DEFAULT_SANDBOX_STALE_SECONDS,
        help=("Remove orphaned/paused sandbox containers older than this many "
              f"seconds (default: {DEFAULT_SANDBOX_STALE_SECONDS})"),
    )
    args = parser.parse_args()

    if args.interval < 1 or args.sandbox_stale_seconds < 1:
        raise ValueError("intervals must be >= 1")

    while True:
        stats = run_once(
            args.db,
            openhands_url=args.openhands_url,
            sandbox_stale_seconds=args.sandbox_stale_seconds,
        )
        print("chat_guard: "
              f"orphan_start_tasks={stats.orphan_start_tasks} "
              f"orphan_callbacks={stats.orphan_callbacks} "
              f"orphan_callback_results={stats.orphan_callback_results} "
              f"sandbox_containers_removed={stats.sandbox_containers_removed}")
        if stats.sandbox_cleanup_skipped:
            print(
                f"chat_guard: sandbox_cleanup_skipped={stats.sandbox_cleanup_skipped}"
            )
        if not args.watch:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
