#!/usr/bin/env python3
"""Create and validate the canonical AI Garage workspace tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ops.garage_paths import GarageWorkspacePaths


def bootstrap_workspace(workspace_root: Path | None = None) -> dict[str, object]:
    paths = (
        GarageWorkspacePaths(root=workspace_root.resolve())
        if workspace_root is not None
        else GarageWorkspacePaths.from_env()
    )
    paths.ensure_tree()
    paths.write_path_snapshots()
    paths.touch_bootstrap_marker()
    return {
        "workspace_root": str(paths.root),
        "manifest_path": str(paths.manifest_path()),
        "config_snapshot_path": str(paths.config_snapshot_path()),
        "created": sorted(paths.canonical_paths().items()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="override canonical workspace root",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable output",
    )
    args = parser.parse_args()
    result = bootstrap_workspace(args.workspace_root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"workspace root: {result['workspace_root']}")
        print(f"manifest: {result['manifest_path']}")
        print(f"config snapshot: {result['config_snapshot_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
