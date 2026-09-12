"""Exercise checkpoint training and reloading with synthetic features, never benchmark data."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import torch

from argus.config import ROOT, write_json
from argus.modules.m2_detection import detect
from argus.schema import Features
from argus.train.detector import train


def main() -> None:
    torch.set_num_threads(2)
    output = ROOT / "artifacts/qa/training"
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    rows = []
    for i, split in enumerate(["train"] * 4 + ["val"] * 2 + ["test"] * 2):
        features = rng.normal(size=(8, 16)).astype(np.float32)
        features[:, 0] += (i % 2) * 2
        path = output / f"synthetic-{i}.npy"
        np.save(path, features)
        rows.append(
            {
                "clip_id": f"synthetic-{i}",
                "split": split,
                "label": i % 2,
                "source_dataset": "synthetic-software-test",
                "path_features": path.relative_to(ROOT).as_posix(),
            }
        )
    index = output / "synthetic-index.parquet"
    pd.DataFrame(rows).to_parquet(index, index=False)
    checkpoint = output / "synthetic-detector.pt"
    result = train(index, checkpoint, epochs=1, device="cpu")
    feature = Features(
        cache_path=rows[-1]["path_features"],
        n_snippets=8,
        feature_dim=16,
        extractor="synthetic-software-test",
        cache_key="smoke",
        snippet_s=0.64,
    )
    prediction = detect(feature, ROOT, 5.12, False, checkpoint, "cpu")
    assert len(prediction.score_curve) == 8
    assert all(0 <= score <= 1 for score in prediction.score_curve)
    assert result["test_used_for_selection"] is False
    report = {
        "scope": "SYNTHETIC SOFTWARE TEST ONLY",
        "status": "PASS",
        "training_rows": 4,
        "validation_rows": 2,
        "heldout_prediction_rows": 1,
        "epochs": 1,
        "checkpoint_reload": "PASS",
        "finite_predictions": True,
        "parameters": result["parameters"],
        "test_used_for_selection": False,
        "note": "No UCF or XD benchmark metric was computed or claimed.",
    }
    write_json(ROOT / "artifacts/training-smoke.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
