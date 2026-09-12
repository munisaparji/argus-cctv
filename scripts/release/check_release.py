"""Extract the built release and verify it with the current installed Python dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    destination = ROOT / "artifacts/qa" / f"relocated-{uuid4().hex[:8]}"
    destination.mkdir(parents=True)
    archive = ROOT / "deliverables/ARGUS_Full_Project.zip"
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.namelist():
            if not (destination / member).resolve().is_relative_to(destination.resolve()):
                raise ValueError("Unsafe archive member")
        bundle.extractall(destination)
    project = destination / "ARGUS"
    manifest = json.loads((project / "RELEASE_MANIFEST.json").read_text())
    for item in manifest["files"]:
        assert hashlib.sha256((project / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    assert not (project / "data/argus.sqlite").exists(), "Local state must not ship"
    env = {**os.environ, "ARGUS_ROOT": str(project), "PYTHONPATH": str(project / "src")}
    env.pop("ARGUS_DB", None)
    run = subprocess.run(
        [sys.executable, "-m", "argus.cli", "demo"], cwd=project, env=env, capture_output=True, text=True
    )
    (destination / "bootstrap.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(f"Relocated demo failed. See {destination / 'bootstrap.log'}")
    code = """
import json
from pathlib import Path
import argus
from argus.config import ROOT
from argus.api.app import app
from fastapi.testclient import TestClient
assert Path(argus.__file__).resolve().is_relative_to(ROOT)
with TestClient(app) as client:
    records=client.get('/api/incidents').json()
    assert len(records)==8
    assert client.get('/').status_code==200
    assert client.get('/api/media/'+records[0]['source']['video_path']).status_code==200
    decision=client.post('/api/incidents/'+records[0]['incident_id']+'/decision',json={'decision':'confirm','operator':'release-test','note':'Isolated relocation check'})
    assert decision.status_code==200
    assert decision.json()['human']['state']=='CONFIRMED'
    assert len(client.get('/api/audit').json())==1
print(json.dumps({'incidents':len(records),'media':'PASS','api':'PASS','audit':'PASS','isolated_source_import':'PASS'}))
"""
    check = subprocess.run([sys.executable, "-c", code], cwd=project, env=env, capture_output=True, text=True)
    (destination / "api-check.log").write_text(check.stdout + check.stderr, encoding="utf-8")
    if check.returncode:
        raise RuntimeError(f"Relocated API failed. See {destination / 'api-check.log'}")
    result = {
        "status": "PASS",
        "archive_integrity": "PASS",
        "file_count": len(manifest["files"]),
        "relocated_demo": "PASS",
        "relocated_api": json.loads(check.stdout),
        "scope": "Fresh extracted files using dependencies installed on this Windows machine. No claim of an independent OS or fresh dependency installation.",
    }
    (ROOT / "artifacts/release-check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
