#!/usr/bin/env python3
"""Canonical AI Garage workspace path resolver and bootstrap helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "workspace"


CANONICAL_DIRS: tuple[str, ...] = (
    "system",
    "system/compose",
    "system/env",
    "system/logs",
    "system/health",
    "system/run",
    "system/tmp",
    "services",
    "services/openwebui",
    "services/openhands",
    "services/stagehand",
    "services/alfred",
    "services/ledger",
    "services/transfer",
    "roles",
    "roles/jarvis",
    "roles/jarvis/sessions",
    "roles/jarvis/memory",
    "roles/jarvis/profiles",
    "roles/jarvis/scratch",
    "roles/jarvis/runtime",
    "roles/robin",
    "roles/robin/sessions",
    "roles/robin/memory",
    "roles/robin/profiles",
    "roles/robin/scratch",
    "roles/robin/runtime",
    "roles/alfred",
    "roles/alfred/runtime",
    "roles/alfred/queues",
    "roles/alfred/checkpoints",
    "roles/alfred/manifests",
    "roles/alfred/logs",
    "ledger",
    "ledger/db",
    "ledger/events",
    "ledger/indexes",
    "ledger/indexes/tasks",
    "ledger/indexes/jobs",
    "ledger/indexes/plans",
    "ledger/indexes/checkpoints",
    "ledger/indexes/continuations",
    "ledger/indexes/artifacts",
    "ledger/indexes/handoffs",
    "ledger/indexes/memory",
    "ledger/artifacts",
    "ledger/artifacts/by_task",
    "ledger/artifacts/by_job",
    "ledger/artifacts/by_type",
    "ledger/artifacts/by_date",
    "ledger/downloads",
    "ledger/downloads/raw",
    "ledger/downloads/classified",
    "ledger/downloads/quarantine",
    "ledger/handoffs",
    "ledger/handoffs/incoming",
    "ledger/handoffs/outgoing",
    "ledger/handoffs/archived",
    "ledger/memory",
    "ledger/memory/global",
    "ledger/memory/jarvis",
    "ledger/memory/robin",
    "ledger/memory/tasks",
    "ledger/memory/sessions",
    "ledger/checkpoints",
    "ledger/checkpoints/tasks",
    "ledger/checkpoints/jobs",
    "ledger/checkpoints/recovery",
    "ledger/plans",
    "ledger/plans/active",
    "ledger/plans/history",
    "ledger/tasks",
    "ledger/tasks/active",
    "ledger/tasks/archived",
    "ledger/exports",
    "ledger/imports",
    "ledger/configs",
    "ledger/snapshots",
    "ledger/backups",
    "ledger/reports",
    "projects",
    "projects/active",
    "projects/archived",
    "jobs",
    "jobs/active",
    "jobs/archived",
    "pobox",
    "pobox/inbound",
    "pobox/outbound",
    "pobox/manifests",
    "pobox/quarantine",
    "shared",
    "shared/inbox",
    "shared/outbox",
    "shared/handoff_staging",
    "shared/download_staging",
    "shared/export_staging",
    "shared/evidence_staging",
)


def _workspace_root_from_env() -> Path:
    raw = os.getenv("GARAGE_WORKSPACE_ROOT")
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_WORKSPACE_ROOT.resolve()


@dataclass(frozen=True)
class GarageWorkspacePaths:
    """Convenience accessor for the canonical workspace tree."""

    root: Path

    @classmethod
    def from_env(cls) -> "GarageWorkspacePaths":
        return cls(root=_workspace_root_from_env())

    @property
    def system(self) -> Path:
        return self.root / "system"

    @property
    def services(self) -> Path:
        return self.root / "services"

    @property
    def roles(self) -> Path:
        return self.root / "roles"

    @property
    def ledger(self) -> Path:
        return self.root / "ledger"

    @property
    def projects(self) -> Path:
        return self.root / "projects"

    @property
    def jobs(self) -> Path:
        return self.root / "jobs"

    @property
    def pobox(self) -> Path:
        return self.root / "pobox"

    @property
    def shared(self) -> Path:
        return self.root / "shared"

    @property
    def ledger_db(self) -> Path:
        return self.ledger / "db"

    @property
    def ledger_events(self) -> Path:
        return self.ledger / "events"

    @property
    def ledger_indexes(self) -> Path:
        return self.ledger / "indexes"

    @property
    def ledger_artifacts(self) -> Path:
        return self.ledger / "artifacts"

    @property
    def ledger_downloads(self) -> Path:
        return self.ledger / "downloads"

    @property
    def ledger_imports(self) -> Path:
        return self.ledger / "imports"

    @property
    def ledger_exports(self) -> Path:
        return self.ledger / "exports"

    @property
    def ledger_configs(self) -> Path:
        return self.ledger / "configs"

    @property
    def ledger_snapshots(self) -> Path:
        return self.ledger / "snapshots"

    @property
    def system_compose(self) -> Path:
        return self.system / "compose"

    def service_root(self, name: str) -> Path:
        return self.services / name

    def role_root(self, name: str) -> Path:
        return self.roles / name

    def role_scratch(self, name: str) -> Path:
        return self.role_root(name) / "scratch"

    def ensure_tree(self) -> None:
        for relative in CANONICAL_DIRS:
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def manifest_path(self) -> Path:
        return self.system_compose / "runtime_workspace_manifest.json"

    def config_snapshot_path(self) -> Path:
        return self.ledger_configs / "runtime_workspace_paths.json"

    def canonical_paths(self) -> dict[str, str]:
        return {
            "root": str(self.root),
            "system": str(self.system),
            "services": str(self.services),
            "roles": str(self.roles),
            "ledger": str(self.ledger),
            "ledger_db": str(self.ledger_db),
            "ledger_events": str(self.ledger_events),
            "ledger_indexes": str(self.ledger_indexes),
            "ledger_artifacts": str(self.ledger_artifacts),
            "projects": str(self.projects),
            "jobs": str(self.jobs),
            "pobox": str(self.pobox),
            "shared": str(self.shared),
        }

    def allowed_artifact_source_roots(self) -> tuple[Path, ...]:
        return (
            self.role_root("jarvis"),
            self.role_root("robin"),
            self.shared,
            self.jobs,
            self.projects,
        )

    def validate_under_workspace(self, candidate: Path) -> Path:
        resolved = candidate.expanduser().resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(
                f"path is outside canonical workspace root: {resolved}"
            ) from exc
        return resolved

    def classify_source_role(self, candidate: Path) -> str:
        resolved = candidate.resolve()
        roots = {
            "jarvis": self.role_root("jarvis"),
            "robin": self.role_root("robin"),
            "shared": self.shared,
            "jobs": self.jobs,
            "projects": self.projects,
            "alfred": self.role_root("alfred"),
            "ledger": self.ledger,
            "pobox": self.pobox,
        }
        for label, root in roots.items():
            try:
                resolved.relative_to(root.resolve())
                return label
            except ValueError:
                continue
        return "unknown"

    def write_path_snapshots(self) -> None:
        payload = {
            "workspace_root": str(self.root),
            "canonical_dirs": list(CANONICAL_DIRS),
            "paths": self.canonical_paths(),
        }
        self.manifest_path().write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.config_snapshot_path().write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def touch_bootstrap_marker(self) -> None:
        marker = self.system / "health" / "workspace_bootstrap.ok"
        marker.write_text("ok\n", encoding="utf-8")


def iter_canonical_dirs(root: Path) -> Iterable[Path]:
    for relative in CANONICAL_DIRS:
        yield root / relative
