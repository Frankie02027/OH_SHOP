from pathlib import Path
import json

from ops.garage_workspace_bootstrap import bootstrap_workspace


def test_bootstrap_creates_canonical_manifest(tmp_path: Path) -> None:
    result = bootstrap_workspace(tmp_path)
    manifest_path = Path(result["manifest_path"])
    snapshot_path = Path(result["config_snapshot_path"])
    assert manifest_path.exists()
    assert snapshot_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["workspace_root"] == str(tmp_path)
    assert "ledger_db" in manifest["paths"]
    assert (tmp_path / "ledger" / "db").exists()
    assert (tmp_path / "pobox" / "inbound").exists()
    assert (tmp_path / "shared" / "evidence_staging").exists()
