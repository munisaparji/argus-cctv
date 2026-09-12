from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.tensorboard import SummaryWriter

from argus.config import ROOT, device_name, read_config, seed_all, write_json


class TemporalDetector(nn.Module):
    def __init__(
        self,
        input_dim: int = 512,
        hidden_dim: int = 320,
        layers: int = 4,
        heads: int = 8,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.project = nn.Linear(input_dim, hidden_dim)
        # WHY: LayerNorm avoids class-imbalance-dependent BatchNorm statistics within MIL bags.
        layer = nn.TransformerEncoderLayer(
            hidden_dim, heads, hidden_dim * 4, dropout, batch_first=True, norm_first=True
        )
        self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.attention = nn.Linear(hidden_dim, 1)
        self.classifier = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.project(x)
        position = torch.arange(z.shape[1], device=x.device, dtype=z.dtype)[:, None]
        scale = torch.exp(
            torch.arange(0, z.shape[-1], 2, device=x.device, dtype=z.dtype) * (-math.log(10000) / z.shape[-1])
        )
        encoding = torch.zeros_like(z[0])
        encoding[:, 0::2] = torch.sin(position * scale)
        encoding[:, 1::2] = torch.cos(position * scale)
        z = self.encoder(z + encoding)
        return self.classifier(z).squeeze(-1).sigmoid(), self.attention(z).squeeze(-1).softmax(dim=1)


def mil_loss(
    scores: torch.Tensor, attention: torch.Tensor, label: torch.Tensor, erase_ratio: float = 0.1
) -> torch.Tensor:
    k = max(1, scores.shape[1] // 8)
    pooled = scores.topk(k, dim=1).values.mean(dim=1)
    weighted = (scores * attention).sum(dim=1)
    base = nn.functional.binary_cross_entropy(pooled, label) + 0.2 * nn.functional.binary_cross_entropy(
        weighted, label
    )
    # WHY: Erasing the strongest snippets asks an anomalous bag to expose secondary evidence.
    n_erase = min(scores.shape[1] - 1, max(1, int(scores.shape[1] * erase_ratio)))
    if n_erase > 0:
        mask = torch.ones_like(scores, dtype=torch.bool)
        mask.scatter_(1, scores.topk(n_erase, dim=1).indices, False)
        remaining = scores.masked_select(mask).reshape(scores.shape[0], -1)
        erased = remaining.topk(min(k, remaining.shape[1]), dim=1).values.mean(dim=1)
        base = base + 0.2 * nn.functional.binary_cross_entropy(erased, label)
    smooth = (scores[:, 1:] - scores[:, :-1]).square().mean() if scores.shape[1] > 1 else scores.sum() * 0
    return base + 0.001 * scores.mean() + 0.01 * smooth


def load_feature(row: dict[str, Any], max_snippets: int | None = None) -> np.ndarray[Any, Any]:
    values = np.load(ROOT / row["path_features"], allow_pickle=False).astype(np.float32)
    if values.ndim != 2 or not len(values) or not np.isfinite(values).all():
        raise ValueError(f"Expected finite [snippets, dimension] features: {row['clip_id']}")
    if max_snippets and len(values) > max_snippets:
        # WHY: Equal temporal bins preserve the whole bag instead of truncating late incidents.
        bins = np.array_split(values, max_snippets)
        values = np.stack([part.mean(axis=0) for part in bins])
    return values


def train(index: Path, output: Path, epochs: int = 30, device: str = "auto") -> dict[str, Any]:
    import pandas as pd

    seed_all(42)
    torch.manual_seed(42)
    selected_device = device_name(device)
    rows = pd.read_parquet(index).to_dict("records")
    training = [r for r in rows if r["split"] == "train"]
    validation = [r for r in rows if r["split"] == "val"]
    if not training or not validation or len({r["label"] for r in training}) != 2:
        raise ValueError("Training requires both labels and an independent validation split")
    if any(r["source_dataset"].lower().startswith("xd") for r in training):
        raise ValueError("XD-Violence is held out; training on it is forbidden")
    groups = [{r["clip_id"] for r in rows if r["split"] == s} for s in ["train", "val", "test"]]
    if any(groups[i] & groups[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("Clip leakage across splits")
    cfg = read_config("model/detector.yaml")
    model_config = {k: cfg[k] for k in ["input_dim", "hidden_dim", "layers", "heads", "dropout"]}
    model_config["input_dim"] = load_feature(training[0]).shape[1]
    model = TemporalDetector(**model_config).to(selected_device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"])
    output.parent.mkdir(parents=True, exist_ok=True)
    history = []
    best = float("inf")
    writer = SummaryWriter(str(output.parent / "tensorboard"))
    try:
        for epoch in range(epochs):
            model.train()
            losses = []
            order = np.random.permutation(len(training))
            for i in order:
                row = training[i]
                x = torch.tensor(load_feature(row, cfg["max_snippets"])[None], device=selected_device)
                y = torch.tensor([float(row["label"])], device=selected_device)
                optimizer.zero_grad()
                scores, attention = model(x)
                loss = mil_loss(scores, attention, y)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1)
                optimizer.step()
                losses.append(float(loss.detach()))
            model.eval()
            val = []
            with torch.inference_mode():
                for row in validation:
                    x = torch.tensor(load_feature(row, cfg["max_snippets"])[None], device=selected_device)
                    scores, attention = model(x)
                    val.append(
                        float(
                            mil_loss(
                                scores, attention, torch.tensor([float(row["label"])], device=selected_device)
                            )
                        )
                    )
            row_metrics = {
                "epoch": epoch + 1,
                "train_loss": float(np.mean(losses)),
                "val_loss": float(np.mean(val)),
            }
            history.append(row_metrics)
            for key in ["train_loss", "val_loss"]:
                writer.add_scalar(key, row_metrics[key], epoch + 1)
            if row_metrics["val_loss"] < best:
                best = row_metrics["val_loss"]
                torch.save(
                    {
                        "model": model.state_dict(),
                        "model_config": model_config,
                        "version": "temporal-mil-v1",
                        "epoch": epoch + 1,
                        "seed": 42,
                        "train_clip_ids": sorted(groups[0]),
                        "val_clip_ids": sorted(groups[1]),
                    },
                    output,
                )
            print(json.dumps(row_metrics))
    finally:
        writer.close()
    result = {
        "history": history,
        "parameters": sum(p.numel() for p in model.parameters()),
        "checkpoint": str(output),
        "test_used_for_selection": False,
    }
    write_json(output.with_suffix(".json"), result)
    return result
