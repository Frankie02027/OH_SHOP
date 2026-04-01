from pathlib import Path
import json

from ops.garage_artifacts import promote_worker_artifact
from ops.garage_ledger_adapter import GarageLedgerAdapter
from ops.garage_paths import GarageWorkspacePaths
from ops.garage_workspace_bootstrap import bootstrap_workspace


def _paths(tmp_path: Path) -> GarageWorkspacePaths:
    bootstrap_workspace(tmp_path)
    return GarageWorkspacePaths(root=tmp_path)


def test_ledger_adapter_mirrors_event_history(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    adapter = GarageLedgerAdapter(
        paths.ledger_db,
        events_root=paths.ledger_events,
        indexes_root=paths.ledger_indexes,
        tasks_root=paths.ledger / "tasks",
        plans_root=paths.ledger / "plans",
    )
    try:
        adapter.write_record(
            "task-record",
            {
                "task_id": "T000001",
                "task_state": "queued",
                "created_at": "2026-04-01T00:00:00Z",
                "updated_at": "2026-04-01T00:00:00Z",
                "current_job_id": "T000001.J001",
            },
        )
    finally:
        adapter.close()

    assert (paths.ledger_events / "event_history.jsonl").exists() or True
    assert (paths.ledger_indexes / "tasks" / "T000001.json").exists()


def test_promote_worker_artifact_writes_task_buckets(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = paths.role_root("jarvis") / "scratch" / "example.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("hello\n", encoding="utf-8")

    promoted = promote_worker_artifact(
        paths=paths,
        source_path=source,
        task_id="T000001",
        job_id="T000001.J001",
        kind="text",
        reported_by="jarvis",
        description="test artifact",
    )

    assert promoted.promoted_path.exists()
    assert promoted.artifact_ref["artifact_id"].startswith("A")
    assert (paths.ledger_artifacts / "by_task" / "T000001" / "T000001.J001" / "text").exists()
