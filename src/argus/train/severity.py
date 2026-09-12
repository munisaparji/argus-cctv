from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from argus.config import read_config, write_json


def fit(rows: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    names = list(read_config("severity_factors.yaml")["factors"])
    training = [r for r in rows if r.get("split") == "train"]
    test_ids = {r["clip_id"] for r in rows if r.get("split") == "test"}
    if any(r["clip_id"] in test_ids for r in training):
        raise ValueError("Severity split leakage")
    if len(training) < 8:
        raise ValueError("At least eight training ratings are required; use substantially more for research")
    # WHY: Fit on pipeline-extracted factors, not the annotator's own factor form (which would leak labels).
    x = np.array([[r["pipeline_factors"][name] for name in names] for r in training], dtype=float)
    scores = np.array([r["score"] for r in training], dtype=float)
    if (
        not np.isfinite(x).all()
        or not np.isfinite(scores).all()
        or (x < 0).any()
        or (x > 1).any()
        or (scores < 0).any()
        or (scores > 100).any()
    ):
        raise ValueError("Finite factors in [0,1] and ratings in [0,100] required")
    bands = np.minimum((scores / 25).astype(int), 3)
    if len(set(bands)) < 2:
        raise ValueError("At least two severity bands required")

    def loss(weights: np.ndarray[Any, Any]) -> float:
        predicted = x @ weights
        cumulative = expit((np.array([25, 50, 75])[None, :] - predicted[:, None]) / 10)
        probabilities = np.diff(
            np.concatenate([np.zeros((len(x), 1)), cumulative, np.ones((len(x), 1))], axis=1), axis=1
        )
        ordinal = -np.log(np.clip(probabilities[np.arange(len(x)), bands], 1e-9, 1)).mean()
        return float(ordinal + 0.001 * np.mean((predicted - scores) ** 2) + 0.0001 * np.sum(weights**2))

    result = minimize(
        loss,
        np.full(13, 100 / 13),
        method="SLSQP",
        bounds=[(0, 100)] * 13,
        constraints=[{"type": "ineq", "fun": lambda w: 100 - w.sum()}],
        options={"maxiter": 3000, "ftol": 1e-9},
    )
    if not result.success:
        raise RuntimeError(f"Severity fit failed: {result.message}")
    synthetic = any(r.get("sample", False) for r in training)
    model = {
        "version": "ordinal-constrained-v1",
        "weights": dict(zip(names, result.x.tolist(), strict=False)),
        "calibration_status": "SYNTHETIC FIT ONLY"
        if synthetic
        else "FITTED on human training ratings; inspect held-out evaluation",
        "train_clip_ids": [r["clip_id"] for r in training],
        "objective": float(result.fun),
        "n_train": len(training),
        "thresholds": [25, 50, 75],
        "link_scale": 10,
    }
    write_json(output, model)
    return model
