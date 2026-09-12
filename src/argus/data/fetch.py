from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd

from argus.config import ROOT, read_config, write_json

INDEX_COLUMNS = [
    "clip_id",
    "source_dataset",
    "split",
    "label",
    "category",
    "duration_s",
    "fps",
    "path_video",
    "path_features",
    "has_captions",
    "has_sirb_labels",
]


def checksum(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(url: str, destination: Path, expected_sha256: str, resume: bool = True) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
        raise ValueError("A trusted expected SHA256 is required before downloading")
    if destination.exists() and checksum(destination) == expected_sha256.lower():
        return expected_sha256.lower()
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if resume and partial.exists() else 0
    request = urllib.request.Request(url, headers={"Range": f"bytes={offset}-"} if offset else {})
    with urllib.request.urlopen(request, timeout=60) as response:
        append = offset > 0 and response.status == 206
        if append and not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
            raise ValueError("Server returned an invalid resume range")
        with partial.open("ab" if append else "wb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
    actual = checksum(partial)
    if actual != expected_sha256.lower():
        raise ValueError(f"SHA256 mismatch: expected {expected_sha256}, got {actual}; partial retained")
    partial.replace(destination)
    return actual


def normalise_index(dataset: str, csv_path: Path) -> Path:
    frame = pd.read_csv(csv_path)
    missing = set(INDEX_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing index columns: {sorted(missing)}")
    if frame.clip_id.duplicated().any() or not frame.split.isin(["train", "val", "test", "demo"]).all():
        raise ValueError("Unique clip IDs and valid splits required")
    if not frame.label.isin([0, 1]).all() or (frame.duration_s <= 0).any() or (frame.fps <= 0).any():
        raise ValueError("Invalid labels, duration or FPS")
    if dataset == "xdviolence" and not frame.split.eq("test").all():
        raise ValueError("XD-Violence must remain test-only")
    target = ROOT / "data/index" / f"{dataset}.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(target, index=False)
    return target


def fetch_all(dataset: str | None = None, resume: bool = True) -> list[dict[str, Any]]:
    results = []
    manifest_path = ROOT / "data/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, cfg in read_config("data_sources.yaml").items():
        if dataset and name != dataset:
            continue
        destination = ROOT / "data/raw" / name / cfg["filename"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "dataset": name,
            "status": "MANUAL_REQUIRED",
            "destination": str(destination),
            "instructions": cfg["instructions"],
            "project_url": cfg.get("project_url"),
        }
        try:
            if cfg.get("download_url") and cfg.get("expected_sha256"):
                actual = download(cfg["download_url"], destination, cfg["expected_sha256"], resume)
                manifest[name] = {
                    "file": destination.relative_to(ROOT).as_posix(),
                    "sha256": actual,
                    "trusted_expected": cfg["expected_sha256"],
                    "status": "VERIFIED",
                }
                row["status"] = "VERIFIED"
            elif destination.exists():
                actual = checksum(destination)
                expected = cfg.get("expected_sha256")
                if expected and actual != expected:
                    raise ValueError("Local file SHA256 mismatch")
                manifest[name] = {
                    "file": destination.relative_to(ROOT).as_posix(),
                    "sha256": actual,
                    "status": "VERIFIED" if expected else "RECORDED_NOT_AUTHENTICATED",
                }
                row["status"] = manifest[name]["status"]
            index = destination.parent / "index.csv"
            if index.exists():
                row["index"] = str(normalise_index(name, index))
        except Exception as error:
            row["error"] = str(error)
        results.append(row)
        print(json.dumps(row, indent=2))
    write_json(manifest_path, manifest)
    return results
