import numpy as np
import pytest

from argus.config import read_config
from argus.eval.metrics import agreement, binary_metrics
from argus.modules.m2_detection import temporal_iou
from argus.modules.m4_reasoning import generate_validated


def test_metrics():
    assert binary_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == {"auc": 1.0, "ap": 1.0}
    assert temporal_iou((2, 6), (4, 8)) == pytest.approx(1 / 3)
    assert agreement([0, 30, 60, 90], [0, 30, 60, 90])["cohen_kappa"] == 1
    assert agreement([0, 0], [0, 0])["spearman_rho"] is None


def test_bounded_json_retry():
    calls = []

    def generate(_):
        calls.append(1)
        return "This is not JSON"

    with pytest.raises(ValueError):
        generate_validated(generate, "test")
    assert len(calls) == 3


def test_temporal_model_backward():
    torch = pytest.importorskip("torch")
    from argus.train.detector import TemporalDetector, mil_loss

    model = TemporalDetector(input_dim=16, hidden_dim=32, layers=4, heads=4)
    scores, attention = model(torch.randn(2, 8, 16))
    loss = mil_loss(scores, attention, torch.tensor([0.0, 1.0]))
    loss.backward()
    assert scores.shape == (2, 8)
    assert torch.isfinite(loss)
    assert model.classifier.weight.grad is not None


def test_constrained_severity_fit(tmp_path):
    from argus.train.severity import fit

    names = list(read_config("severity_factors.yaml")["factors"])
    rng = np.random.default_rng(42)
    rows = []
    for i in range(24):
        values = rng.random(13)
        rows.append(
            {
                "clip_id": str(i),
                "split": "train" if i < 20 else "test",
                "pipeline_factors": dict(zip(names, values.tolist(), strict=False)),
                "score": float(values @ np.full(13, 100 / 13)),
                "sample": True,
            }
        )
    model = fit(rows, tmp_path / "severity.json")
    assert all(w >= 0 for w in model["weights"].values())
    assert sum(model["weights"].values()) <= 100.0001
    assert model["calibration_status"] == "SYNTHETIC FIT ONLY"
