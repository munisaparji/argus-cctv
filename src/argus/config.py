from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import yaml

ROOT = Path(os.environ.get("ARGUS_ROOT", Path(__file__).resolve().parents[2])).resolve()


def read_config(name: str) -> dict[str, Any]:
    with (ROOT / "configs" / name).open(encoding="utf-8") as stream:
        return dict(yaml.safe_load(stream))


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    temp.replace(path)


def seed_all(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)


def device_name(requested: str = "auto") -> str:
    if requested not in {"cpu", "cuda", "auto"}:
        raise ValueError("DEVICE must be cpu, cuda or auto")
    if requested == "cpu":
        return "cpu"
    import torch

    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable; set DEVICE=cpu")
    return "cuda" if torch.cuda.is_available() else "cpu"
