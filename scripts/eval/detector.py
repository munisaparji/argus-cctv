from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from argus.config import ROOT, device_name, write_json
from argus.eval.metrics import binary_metrics
from argus.train.detector import TemporalDetector, load_feature


def main(crossdataset: bool = False) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    device = device_name(args.device)
    state = torch.load(args.checkpoint, map_location=device, weights_only=True)
    model = TemporalDetector(**state["model_config"]).to(device)
    model.load_state_dict(state["model"])
    model.eval()
    rows = pd.read_parquet(args.index).to_dict("records")
    rows = [r for r in rows if r["split"] == "test"]
    if not rows:
        raise ValueError("No held-out test rows")
    training_ids = set(state.get("train_clip_ids", [])) | set(state.get("val_clip_ids", []))
    labels, predictions, per_video = [], [], []
    for row in rows:
        if row["clip_id"] in training_ids:
            raise ValueError("Evaluation clip was used for training or model selection")
        if crossdataset and not str(row["source_dataset"]).lower().startswith("xd"):
            raise ValueError("Cross-dataset input must contain XD-Violence only")
        if "path_frame_labels" not in row:
            raise ValueError(
                "Frame AUC/AP requires path_frame_labels in the index; video labels are insufficient"
            )
        truth = np.load(ROOT / row["path_frame_labels"], allow_pickle=False).reshape(-1)
        with torch.inference_mode():
            scores, _ = model(torch.tensor(load_feature(row)[None], device=device))
        values = scores[0].cpu().numpy()
        # WHY: Explicit seconds-per-snippet handles feature rates without silently truncating frames.
        if "snippet_s" not in row:
            raise ValueError("Index must provide snippet_s for exact frame alignment")
        frame_times = np.arange(len(truth)) / float(row["fps"])
        indices = np.minimum((frame_times / float(row["snippet_s"])).astype(int), len(values) - 1)
        frame_scores = values[indices]
        labels.extend(truth.astype(int).tolist())
        predictions.extend(frame_scores.tolist())
        per_video.append({"clip_id": row["clip_id"], "n_frames": len(truth)})
    result = {
        "status": "MEASURED",
        **binary_metrics(labels, predictions),
        "n_frames": len(labels),
        "videos": per_video,
        "primary_metric": "ap" if crossdataset else "auc",
    }
    name = "xd_average_precision" if crossdataset else "ucf_frame_auc"
    write_json(ROOT / "artifacts/research" / f"{name}.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
