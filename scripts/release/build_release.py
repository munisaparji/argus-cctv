"""Create a source-and-demo release with checksums and no local research/private state."""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "deliverables"
ARCHIVE = OUT / "ARGUS_Full_Project.zip"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".codex",
    ".agents",
    "qa",
    ".matplotlib",
    "reference",
    "checkpoints",
    "runs",
}
ROOT_DIRS = {
    ".github",
    "configs",
    "src",
    "scripts",
    "tests",
    "apps",
    "docs",
    "notebooks",
    "artifacts",
    "data",
    "deliverables",
}
DELIVERABLES = {
    "ARGUS_Project_Guide.pdf",
    "ARGUS_Project_Guide.md",
    "ARGUS_Poster.pdf",
    "ARGUS_Review_Deck.pptx",
    "ARGUS_Demo_Walkthrough.webm",
}


def release_files() -> list[Path]:
    files = []
    for directory, children, names in os.walk(ROOT):
        base = Path(directory)
        rel = base.relative_to(ROOT)
        children[:] = sorted(d for d in children if d not in EXCLUDED_DIRS and not d.endswith(".egg-info"))
        if not rel.parts:
            children[:] = [d for d in children if d in ROOT_DIRS]
        elif rel.as_posix() == "data":
            children[:] = [d for d in children if d == "sample"]
            names = []
        elif rel.as_posix() == "deliverables":
            children[:] = []
            names = [name for name in names if name in DELIVERABLES]
        for name in sorted(names):
            path = base / name
            if path.suffix in {".pyc", ".tsbuildinfo", ".sqlite", ".log"} or name.startswith(".env"):
                continue
            if path.is_symlink():
                continue
            files.append(path)
    return sorted(files)


def main() -> None:
    for name in DELIVERABLES:
        if not (OUT / name).is_file():
            raise FileNotFoundError(f"Required deliverable is missing: {name}")
    files = release_files()
    manifest = []
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            name = path.relative_to(ROOT).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.append({"path": name, "sha256": digest, "bytes": path.stat().st_size})
            bundle.write(path, f"ARGUS/{name}")
        bundle.writestr(
            "ARGUS/RELEASE_MANIFEST.json", json.dumps({"version": "1.0.0", "files": manifest}, indent=2)
        )
        bundle.writestr(
            "ARGUS/SHA256SUMS.txt", "\n".join(f"{row['sha256']}  {row['path']}" for row in manifest) + "\n"
        )
    with zipfile.ZipFile(ARCHIVE) as bundle:
        damaged = bundle.testzip()
        if damaged:
            raise ValueError(f"ZIP integrity failed: {damaged}")
        for row in manifest:
            actual = hashlib.sha256(bundle.read(f"ARGUS/{row['path']}")).hexdigest()
            assert actual == row["sha256"], row["path"]
    checksum = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    (OUT / "ARGUS_Full_Project.sha256").write_text(f"{checksum}  {ARCHIVE.name}\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "archive": str(ARCHIVE),
                "files": len(manifest),
                "bytes": ARCHIVE.stat().st_size,
                "sha256": checksum,
                "integrity": "PASS",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
