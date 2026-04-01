#!/usr/bin/env python3
"""Small local storage adapter for Garage canonical state and event history."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable

from ops.garage_alfred import (
    Clock,
    GarageAlfredProcessor,
    GarageOfficialBundle,
)
from ops.garage_runtime import GarageRecordWrite


class GarageStorageError(RuntimeError):
    """Raised when the local Garage storage adapter cannot complete a write/read."""


class GarageStorageAdapter:
    """SQLite + JSONL storage for the first durable Garage record path."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "garage_state.db"
        self.event_log_path = self.root / "event_history.jsonl"
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._pending_counters: dict[str, int] = {}
        self._initialize_storage()

    def close(self) -> None:
        self._conn.close()

    def mint_task_id(self) -> str:
        number = self._reserve_pending_counter("task", self._max_task_number)
        return f"T{number:06d}"

    def mint_job_id(self, task_id: str) -> str:
        number = self._reserve_pending_counter(
            f"job:{task_id}",
            lambda: self._max_job_number(task_id),
        )
        return f"{task_id}.J{number:03d}"

    def mint_event_id(self, task_id: str) -> str:
        number = self._reserve_pending_counter(
            f"event:{task_id}",
            lambda: self._max_event_number(task_id),
        )
        return f"{task_id}.E{number:04d}"

    def mint_checkpoint_id(self, task_id: str) -> str:
        number = self._reserve_pending_counter(
            f"checkpoint:{task_id}",
            lambda: self._max_checkpoint_number(task_id),
        )
        return f"{task_id}.C{number:03d}"

    def write_record(self, schema_name: str, data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        bundle = GarageOfficialBundle(
            call_type="direct-record-write",
            result=(schema_name, data),
            events=(),
            records=(GarageRecordWrite(schema_name, data),),
        )
        _, written_records = self.apply_official_bundle(bundle)
        return written_records[0]

    def apply_official_bundle(
        self,
        bundle: GarageOfficialBundle,
    ) -> tuple[tuple[dict[str, Any], ...], tuple[tuple[str, dict[str, Any]], ...]]:
        try:
            with self._conn:
                for index, record_write in enumerate(bundle.records, start=1):
                    self._before_bundle_record_write(index, record_write, bundle)
                    self._apply_record_write(record_write)
                self._persist_counters_from_bundle(bundle)
        except Exception:
            self._pending_counters.clear()
            raise

        self._pending_counters.clear()
        self._rewrite_event_log_from_sqlite()
        return (
            tuple(dict(event) for event in bundle.events),
            tuple((record.schema_name, dict(record.data)) for record in bundle.records),
        )

    def read_task_record(self, task_id: str) -> dict[str, Any] | None:
        return self._read_json_record("task_records", "task_id", task_id)

    def read_job_record(self, job_id: str) -> dict[str, Any] | None:
        return self._read_json_record("job_records", "job_id", job_id)

    def read_checkpoint_record(self, checkpoint_id: str) -> dict[str, Any] | None:
        return self._read_json_record("checkpoint_records", "checkpoint_id", checkpoint_id)

    def read_tracked_plan(self, task_id: str, plan_version: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            """
            SELECT data_json
            FROM tracked_plans
            WHERE task_id = ? AND plan_version = ?
            """,
            (task_id, plan_version),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["data_json"])

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

    def list_artifact_index_records(
        self,
        *,
        task_id: str | None = None,
        job_id: str | None = None,
        event_id: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT data_json FROM artifact_index_records ORDER BY artifact_id ASC"
        ).fetchall()
        records = [json.loads(row["data_json"]) for row in rows]
        filtered: list[dict[str, Any]] = []
        for record in records:
            if task_id is not None and record.get("task_id") != task_id:
                continue
            if job_id is not None and record.get("job_id") != job_id:
                continue
            if event_id is not None and record.get("event_id") != event_id:
                continue
            filtered.append(record)
        return filtered

    def read_event_history(
        self,
        task_id: str | None = None,
        job_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT data_json FROM event_records"
        conditions: list[str] = []
        params: list[Any] = []
        if task_id is not None:
            conditions.append("task_id = ?")
            params.append(task_id)
        if job_id is not None:
            conditions.append("job_id = ?")
            params.append(job_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY row_id ASC"
        rows = self._conn.execute(query, tuple(params)).fetchall()
        return [json.loads(row["data_json"]) for row in rows]

    def peek_next_task_id(self) -> str:
        return f"T{self._current_counter_value('task', self._max_task_number):06d}"

    def peek_next_event_id(self, task_id: str) -> str:
        value = self._current_counter_value(f"event:{task_id}", lambda: self._max_event_number(task_id))
        return f"{task_id}.E{value:04d}"

    def peek_next_job_id(self, task_id: str) -> str:
        value = self._current_counter_value(
            f"job:{task_id}",
            lambda: self._max_job_number(task_id),
        )
        return f"{task_id}.J{value:03d}"

    def peek_next_checkpoint_id(self, task_id: str) -> str:
        value = self._current_counter_value(
            f"checkpoint:{task_id}",
            lambda: self._max_checkpoint_number(task_id),
        )
        return f"{task_id}.C{value:03d}"

    def list_child_jobs(self, parent_job_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT data_json FROM job_records ORDER BY job_id ASC"
        ).fetchall()
        records = [json.loads(row["data_json"]) for row in rows]
        return [
            record
            for record in records
            if record.get("parent_job_id") == parent_job_id
        ]

    def latest_attempt_for_job(self, job_id: str) -> int | None:
        job_record = self.read_job_record(job_id)
        if job_record is None:
            return None
        history = self.read_event_history(job_id=job_id)
        started_attempts = [
            int(event["attempt_no"])
            for event in history
            if event.get("event_type") == "job.started" and "attempt_no" in event
        ]
        record_attempt = int(job_record.get("attempt_no") or 1)
        return max([record_attempt, *started_attempts])

    def latest_continuation_for_task(self, task_id: str) -> dict[str, Any] | None:
        continuations = self.list_continuation_records(task_id)
        if not continuations:
            return None
        return continuations[-1]

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

            CREATE TABLE IF NOT EXISTS tracked_plans (
                task_id TEXT NOT NULL,
                plan_version INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                PRIMARY KEY(task_id, plan_version)
            );

            CREATE TABLE IF NOT EXISTS continuation_records (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                job_id TEXT,
                created_at TEXT NOT NULL,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS event_records (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                task_id TEXT NOT NULL,
                job_id TEXT,
                recorded_at TEXT NOT NULL,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifact_index_records (
                artifact_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def _reserve_pending_counter(self, scope: str, seed_func: Callable[[], int]) -> int:
        if scope in self._pending_counters:
            current_value = self._pending_counters[scope]
        else:
            current_value = self._current_counter_value(scope, seed_func)
        self._pending_counters[scope] = current_value + 1
        return current_value

    def _current_counter_value(self, scope: str, seed_func: Callable[[], int]) -> int:
        current_row = self._conn.execute(
            "SELECT next_value FROM id_counters WHERE scope = ?",
            (scope,),
        ).fetchone()
        if current_row is None:
            return max(1, int(seed_func()) + 1)
        return int(current_row["next_value"])

    def _max_task_number(self) -> int:
        row = self._conn.execute("SELECT task_id FROM task_records ORDER BY task_id DESC LIMIT 1").fetchone()
        if row is None:
            return 0
        return int(str(row["task_id"])[1:])

    def _max_job_number(self, task_id: str) -> int:
        rows = self._conn.execute(
            "SELECT data_json FROM job_records ORDER BY job_id DESC"
        ).fetchall()
        job_ids = [
            json.loads(row["data_json"])["job_id"]
            for row in rows
            if json.loads(row["data_json"]).get("task_id") == task_id
        ]
        if not job_ids:
            return 0
        return int(str(job_ids[0]).split(".J", 1)[1])

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
        row = self._conn.execute(
            """
            SELECT event_id
            FROM event_records
            WHERE task_id = ?
            ORDER BY row_id DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            return 0
        return int(str(row["event_id"]).split(".E", 1)[1])

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

    def _apply_record_write(self, record_write: GarageRecordWrite) -> None:
        schema_name = record_write.schema_name
        data = record_write.data
        if schema_name == "task-record":
            self._upsert_json_record("task_records", "task_id", data["task_id"], data)
        elif schema_name == "job-record":
            self._upsert_json_record("job_records", "job_id", data["job_id"], data)
        elif schema_name == "tracked-plan":
            self._upsert_tracked_plan(data)
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
            self._insert_event_record(data)
        else:
            raise GarageStorageError(f"Unsupported schema_name for storage: {schema_name}")

    def _insert_event_record(self, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO event_records(event_id, task_id, job_id, recorded_at, data_json)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                data["event_id"],
                data["task_id"],
                data.get("job_id"),
                data["recorded_at"],
                json.dumps(data, sort_keys=True),
            ),
        )

    def _upsert_tracked_plan(self, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO tracked_plans(task_id, plan_version, data_json)
            VALUES(?, ?, ?)
            ON CONFLICT(task_id, plan_version) DO UPDATE SET data_json = excluded.data_json
            """,
            (
                data["task_id"],
                data["plan_version"],
                json.dumps(data, sort_keys=True),
            ),
        )

    def _persist_counters_from_bundle(self, bundle: GarageOfficialBundle) -> None:
        next_values: dict[str, int] = {}
        for record in bundle.records:
            if record.schema_name == "task-record":
                task_id = record.data["task_id"]
                next_values["task"] = max(
                    next_values.get("task", 1),
                    int(str(task_id)[1:]) + 1,
                )
            elif record.schema_name == "job-record":
                job_id = record.data["job_id"]
                task_id = record.data["task_id"]
                next_values[f"job:{task_id}"] = max(
                    next_values.get(f"job:{task_id}", 1),
                    int(str(job_id).split(".J", 1)[1]) + 1,
                )
            elif record.schema_name == "checkpoint-record":
                checkpoint_id = record.data["checkpoint_id"]
                task_id = record.data["task_id"]
                next_values[f"checkpoint:{task_id}"] = max(
                    next_values.get(f"checkpoint:{task_id}", 1),
                    int(str(checkpoint_id).split(".C", 1)[1]) + 1,
                )
            elif record.schema_name == "event-record":
                event_id = record.data["event_id"]
                task_id = record.data["task_id"]
                next_values[f"event:{task_id}"] = max(
                    next_values.get(f"event:{task_id}", 1),
                    int(str(event_id).split(".E", 1)[1]) + 1,
                )

        for scope, next_value in next_values.items():
            current_next = self._current_counter_value(scope, lambda: 0)
            persisted_next = max(current_next, next_value)
            self._conn.execute(
                """
                INSERT INTO id_counters(scope, next_value)
                VALUES(?, ?)
                ON CONFLICT(scope) DO UPDATE SET next_value = excluded.next_value
                """,
                (scope, persisted_next),
            )

    def _rewrite_event_log_from_sqlite(self) -> None:
        rows = self._conn.execute(
            "SELECT data_json FROM event_records ORDER BY row_id ASC"
        ).fetchall()
        with self.event_log_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(row["data_json"])
                handle.write("\n")

    def _before_bundle_record_write(
        self,
        index: int,
        record_write: GarageRecordWrite,
        bundle: GarageOfficialBundle,
    ) -> None:
        """Protected hook for narrow failure-in-transaction tests."""
        return None


def build_storage_backed_alfred_processor(
    storage_root: Path | str,
    *,
    now_provider: Clock | None = None,
) -> tuple[GarageStorageAdapter, GarageAlfredProcessor]:
    """Create a storage-backed Alfred processor and its adapter."""

    storage = GarageStorageAdapter(storage_root)
    processor = GarageAlfredProcessor(
        bundle_applier=storage.apply_official_bundle,
        id_allocator=storage,
        state_reader=storage,
        now_provider=now_provider,
    )
    return storage, processor


__all__ = [
    "GarageStorageAdapter",
    "GarageStorageError",
    "build_storage_backed_alfred_processor",
]
