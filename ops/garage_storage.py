#!/usr/bin/env python3
"""Small local storage adapter for Garage canonical state and event history."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ops.garage_alfred import Clock, GarageAlfredProcessor


class GarageStorageError(RuntimeError):
    """Raised when the local Garage storage adapter cannot complete a write/read."""


class GarageStorageAdapter:
    """SQLite + JSONL storage for the first durable Garage record path."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "garage_state.db"
        self.event_log_path = self.root / "event_history.jsonl"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._initialize_storage()

    def close(self) -> None:
        self._conn.close()

    def mint_task_id(self) -> str:
        number = self._reserve_counter("task", self._max_task_number)
        return f"T{number:06d}"

    def mint_event_id(self, task_id: str) -> str:
        number = self._reserve_counter(
            f"event:{task_id}",
            lambda: self._max_event_number(task_id),
        )
        return f"{task_id}.E{number:04d}"

    def mint_checkpoint_id(self, task_id: str) -> str:
        number = self._reserve_counter(
            f"checkpoint:{task_id}",
            lambda: self._max_checkpoint_number(task_id),
        )
        return f"{task_id}.C{number:03d}"

    def write_record(self, schema_name: str, data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        if schema_name == "task-record":
            self._upsert_json_record("task_records", "task_id", data["task_id"], data)
        elif schema_name == "job-record":
            self._upsert_json_record("job_records", "job_id", data["job_id"], data)
        elif schema_name == "checkpoint-record":
            self._upsert_json_record(
                "checkpoint_records",
                "checkpoint_id",
                data["checkpoint_id"],
                data,
            )
        elif schema_name == "continuation-record":
            self._insert_continuation_record(data)
        elif schema_name == "artifact-index-record":
            self._upsert_json_record(
                "artifact_index_records",
                "artifact_id",
                data["artifact_id"],
                data,
            )
        elif schema_name == "event-record":
            self._append_event_record(data)
        else:
            raise GarageStorageError(f"Unsupported schema_name for storage: {schema_name}")
        return (schema_name, data)

    def read_task_record(self, task_id: str) -> dict[str, Any] | None:
        return self._read_json_record("task_records", "task_id", task_id)

    def read_job_record(self, job_id: str) -> dict[str, Any] | None:
        return self._read_json_record("job_records", "job_id", job_id)

    def read_checkpoint_record(self, checkpoint_id: str) -> dict[str, Any] | None:
        return self._read_json_record("checkpoint_records", "checkpoint_id", checkpoint_id)

    def list_continuation_records(self, task_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT data_json FROM continuation_records"
        params: tuple[Any, ...] = ()
        if task_id is not None:
            query += " WHERE task_id = ?"
            params = (task_id,)
        query += " ORDER BY row_id ASC"
        rows = self._conn.execute(query, params).fetchall()
        return [json.loads(row["data_json"]) for row in rows]

    def read_artifact_index_record(self, artifact_id: str) -> dict[str, Any] | None:
        return self._read_json_record(
            "artifact_index_records",
            "artifact_id",
            artifact_id,
        )

    def read_event_history(self, task_id: str | None = None) -> list[dict[str, Any]]:
        if not self.event_log_path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.event_log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if task_id is None or event.get("task_id") == task_id:
                    events.append(event)
        return events

    def _initialize_storage(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS id_counters (
                scope TEXT PRIMARY KEY,
                next_value INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS task_records (
                task_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_records (
                job_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checkpoint_records (
                checkpoint_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS continuation_records (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                job_id TEXT,
                created_at TEXT NOT NULL,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifact_index_records (
                artifact_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def _reserve_counter(self, scope: str, seed_func: callable) -> int:
        current_row = self._conn.execute(
            "SELECT next_value FROM id_counters WHERE scope = ?",
            (scope,),
        ).fetchone()
        if current_row is None:
            current_value = max(1, int(seed_func()) + 1)
        else:
            current_value = int(current_row["next_value"])
        self._conn.execute(
            """
            INSERT INTO id_counters(scope, next_value)
            VALUES(?, ?)
            ON CONFLICT(scope) DO UPDATE SET next_value = excluded.next_value
            """,
            (scope, current_value + 1),
        )
        self._conn.commit()
        return current_value

    def _max_task_number(self) -> int:
        row = self._conn.execute("SELECT task_id FROM task_records ORDER BY task_id DESC LIMIT 1").fetchone()
        if row is None:
            return 0
        return int(str(row["task_id"])[1:])

    def _max_checkpoint_number(self, task_id: str) -> int:
        row = self._conn.execute(
            """
            SELECT checkpoint_id
            FROM checkpoint_records
            WHERE checkpoint_id LIKE ?
            ORDER BY checkpoint_id DESC
            LIMIT 1
            """,
            (f"{task_id}.C%",),
        ).fetchone()
        if row is None:
            return 0
        return int(str(row["checkpoint_id"]).split(".C", 1)[1])

    def _max_event_number(self, task_id: str) -> int:
        max_number = 0
        for event in self.read_event_history(task_id):
            event_id = event.get("event_id")
            if isinstance(event_id, str) and event_id.startswith(f"{task_id}.E"):
                max_number = max(max_number, int(event_id.split(".E", 1)[1]))
        return max_number

    def _upsert_json_record(
        self,
        table_name: str,
        key_field: str,
        key_value: str,
        data: dict[str, Any],
    ) -> None:
        self._conn.execute(
            f"""
            INSERT INTO {table_name}({key_field}, data_json)
            VALUES(?, ?)
            ON CONFLICT({key_field}) DO UPDATE SET data_json = excluded.data_json
            """,
            (key_value, json.dumps(data, sort_keys=True)),
        )
        self._conn.commit()

    def _insert_continuation_record(self, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO continuation_records(task_id, job_id, created_at, data_json)
            VALUES(?, ?, ?, ?)
            """,
            (
                data["task_id"],
                data.get("job_id"),
                data["created_at"],
                json.dumps(data, sort_keys=True),
            ),
        )
        self._conn.commit()

    def _append_event_record(self, data: dict[str, Any]) -> None:
        with self.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(data, sort_keys=True))
            handle.write("\n")

    def _read_json_record(
        self,
        table_name: str,
        key_field: str,
        key_value: str,
    ) -> dict[str, Any] | None:
        row = self._conn.execute(
            f"SELECT data_json FROM {table_name} WHERE {key_field} = ?",
            (key_value,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["data_json"])


def build_storage_backed_alfred_processor(
    storage_root: Path | str,
    *,
    now_provider: Clock | None = None,
) -> tuple[GarageStorageAdapter, GarageAlfredProcessor]:
    """Create a storage-backed Alfred processor and its adapter."""

    storage = GarageStorageAdapter(storage_root)
    processor = GarageAlfredProcessor(
        record_writer=storage.write_record,
        id_allocator=storage,
        now_provider=now_provider,
    )
    return storage, processor


__all__ = [
    "GarageStorageAdapter",
    "GarageStorageError",
    "build_storage_backed_alfred_processor",
]
