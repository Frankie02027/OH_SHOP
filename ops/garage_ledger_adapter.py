#!/usr/bin/env python3
"""Bridge the current SQLite+JSONL storage slice into the canonical ledger tree."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

from ops.garage_storage import GarageStorageAdapter


class GarageLedgerAdapter(GarageStorageAdapter):
    """Persist current Garage records and mirror them into canonical ledger views."""

    def __init__(
        self,
        db_root: Path | str,
        *,
        events_root: Path | str,
        indexes_root: Path | str,
        tasks_root: Path | str | None = None,
        plans_root: Path | str | None = None,
    ) -> None:
        self._events_root = Path(events_root)
        self._indexes_root = Path(indexes_root)
        self._tasks_root = Path(tasks_root) if tasks_root is not None else None
        self._plans_root = Path(plans_root) if plans_root is not None else None
        self._events_root.mkdir(parents=True, exist_ok=True)
        self._indexes_root.mkdir(parents=True, exist_ok=True)
        super().__init__(db_root)
        self._mirror_event_history()

    def apply_official_bundle(
        self,
        bundle: Any,
    ) -> tuple[tuple[dict[str, Any], ...], tuple[tuple[str, dict[str, Any]], ...]]:
        result = super().apply_official_bundle(bundle)
        for schema_name, record in result[1]:
            self._mirror_record(schema_name, record)
        self._mirror_event_history()
        return result

    def write_record(self, schema_name: str, data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        written = super().write_record(schema_name, data)
        self._mirror_record(written[0], written[1])
        self._mirror_event_history()
        return written

    def _mirror_event_history(self) -> None:
        if self.event_log_path.exists():
            target = self._events_root / "event_history.jsonl"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.event_log_path, target)

    def _mirror_record(self, schema_name: str, record: dict[str, Any]) -> None:
        writer = {
            "task-record": self._mirror_task_record,
            "job-record": self._mirror_job_record,
            "tracked-plan": self._mirror_plan_record,
            "checkpoint-record": self._mirror_checkpoint_record,
            "continuation-record": self._mirror_continuation_record,
            "artifact-index-record": self._mirror_artifact_record,
            "handoff-record": self._mirror_handoff_record,
            "memory-record": self._mirror_memory_record,
        }.get(schema_name)
        if writer is None:
            self._mirror_misc_record(schema_name, record)
            return
        writer(record)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _mirror_task_record(self, record: dict[str, Any]) -> None:
        task_id = str(record["task_id"])
        self._write_json(self._indexes_root / "tasks" / f"{task_id}.json", record)
        if self._tasks_root is not None:
            state = str(record.get("task_state") or "active")
            bucket = "archived" if state in {"completed", "failed", "cancelled"} else "active"
            self._write_json(self._tasks_root / bucket / task_id / "task_record.json", record)

    def _mirror_job_record(self, record: dict[str, Any]) -> None:
        job_id = str(record["job_id"])
        self._write_json(self._indexes_root / "jobs" / f"{job_id}.json", record)
        task_id = str(record.get("task_id") or job_id.split(".")[0])
        if self._tasks_root is not None:
            self._write_json(
                self._tasks_root / "active" / task_id / "manifests" / f"{job_id}.json",
                record,
            )

    def _mirror_plan_record(self, record: dict[str, Any]) -> None:
        task_id = str(record["task_id"])
        plan_version = int(record["plan_version"])
        filename = f"{task_id}__v{plan_version}.json"
        self._write_json(self._indexes_root / "plans" / filename, record)
        if self._plans_root is not None:
            self._write_json(self._plans_root / "history" / filename, record)
            if str(record.get("plan_status")) == "active":
                self._write_json(self._plans_root / "active" / f"{task_id}.json", record)

    def _mirror_checkpoint_record(self, record: dict[str, Any]) -> None:
        checkpoint_id = str(record["checkpoint_id"])
        self._write_json(self._indexes_root / "checkpoints" / f"{checkpoint_id}.json", record)

    def _mirror_continuation_record(self, record: dict[str, Any]) -> None:
        task_id = str(record["task_id"])
        label = str(record.get("recorded_at") or record.get("created_at") or "latest").replace(":", "-")
        self._write_json(self._indexes_root / "continuations" / task_id / f"{label}.json", record)

    def _mirror_artifact_record(self, record: dict[str, Any]) -> None:
        artifact_id = str(record["artifact_id"])
        self._write_json(self._indexes_root / "artifacts" / f"{artifact_id}.json", record)

    def _mirror_handoff_record(self, record: dict[str, Any]) -> None:
        task_id = str(record.get("task_id") or "unknown-task")
        label = str(record.get("handoff_id") or record.get("job_id") or "handoff")
        self._write_json(self._indexes_root / "handoffs" / task_id / f"{label}.json", record)

    def _mirror_memory_record(self, record: dict[str, Any]) -> None:
        scope = str(record.get("scope") or "global")
        label = str(record.get("memory_id") or record.get("task_id") or "memory")
        self._write_json(self._indexes_root / "memory" / scope / f"{label}.json", record)

    def _mirror_misc_record(self, schema_name: str, record: dict[str, Any]) -> None:
        label = str(record.get("task_id") or record.get("job_id") or record.get("artifact_id") or "record")
        safe_schema = schema_name.replace("/", "_")
        self._write_json(self._indexes_root / "misc" / f"{safe_schema}__{label}.json", record)
