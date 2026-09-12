from __future__ import annotations

from pathlib import Path

import numpy as np

from argus.schema import Features, Localisation


def temporal_iou(predicted: tuple[float, float], truth: tuple[float, float]) -> float:
    overlap = max(0.0, min(predicted[1], truth[1]) - max(predicted[0], truth[0]))
    union = max(predicted[1], truth[1]) - min(predicted[0], truth[0])
    return overlap / union if union > 0 else 0.0


def localise(
    scores: list[float], duration: float, step: float, threshold: float = 0.5
) -> tuple[float, float]:
    active = np.flatnonzero(np.asarray(scores) >= threshold)
    if len(active) == 0:
        return 0.0, duration
    return float(active[0] * step), min(duration, float((active[-1] + 1) * step))


def detect(
    features: Features,
    root: Path,
    duration: float,
    sample: bool,
    checkpoint: Path | None = None,
    device: str = "cpu",
) -> Localisation:
    x = np.load(root / features.cache_path, allow_pickle=False)
    category = "Unclassified"
    if sample:
        # WHY: This transparent motion baseline is labelled SAMPLE, never a trained anomaly detector.
        curve = np.clip(x[:, -1] * 1200, 0.02, 0.98)
        version = "sample-motion-baseline-v1"
        category = "Motion" if float(curve.max()) >= 0.5 else "Normal"
    else:
        if checkpoint is None or not checkpoint.is_file():
            raise FileNotFoundError(
                "A trained detector checkpoint is required. Run scripts/train/detector.py"
            )
        import torch

        from argus.train.detector import TemporalDetector

        state = torch.load(checkpoint, map_location=device, weights_only=True)
        model = TemporalDetector(**state["model_config"]).to(device)
        model.load_state_dict(state["model"])
        model.eval()
        with torch.inference_mode():
            scores, _ = model(torch.as_tensor(x[None], device=device))
        curve = scores[0].cpu().numpy()
        version = str(state["version"])
        # WHY: Binary MIL labels do not supervise 13-way incident classification.
    start, end = localise(curve.tolist(), duration, features.snippet_s)
    return Localisation(
        score_curve=curve.tolist(),
        t_start_s=start,
        t_end_s=end,
        incident_class=category,
        class_confidence=float(curve.max()),
        model_version=version,
    )
