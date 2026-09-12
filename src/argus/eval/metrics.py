from __future__ import annotations

from typing import Any

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, cohen_kappa_score, mean_absolute_error, roc_auc_score


def binary_metrics(labels: list[int], scores: list[float]) -> dict[str, float]:
    if len(labels) != len(scores) or len(set(labels)) != 2 or not set(labels) <= {0, 1}:
        raise ValueError("Aligned binary labels and predictions with both classes required")
    return {"auc": float(roc_auc_score(labels, scores)), "ap": float(average_precision_score(labels, scores))}


def agreement(a: list[float], b: list[float]) -> dict[str, Any]:
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("At least two paired ratings required")
    x, y = np.asarray(a), np.asarray(b)
    rho = float(spearmanr(x, y).statistic) if np.std(x) and np.std(y) else None
    x_band, y_band = np.minimum(x // 25, 3), np.minimum(y // 25, 3)
    kappa = float(cohen_kappa_score(x_band, y_band)) if len(set(x_band) | set(y_band)) > 1 else None
    disagreement = float(np.mean((x - y) ** 2))
    pooled = np.concatenate([x, y])
    expected = float(np.sum((pooled[:, None] - pooled[None, :]) ** 2) / (len(pooled) * (len(pooled) - 1)))
    return {
        "n": len(a),
        "cohen_kappa": kappa,
        "spearman_rho": rho,
        "mae": float(mean_absolute_error(x, y)),
        "krippendorff_alpha_interval": 1 - disagreement / expected if expected else None,
    }
