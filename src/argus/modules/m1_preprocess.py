from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from argus.config import ROOT, digest, write_json
from argus.schema import Features


def extract(
    video: Path, sample: bool, device: str = "cpu", model_id: str = "openai/clip-vit-base-patch16"
) -> Features:
    config = {"model": "synthetic-pixels-v1" if sample else model_id, "fps": 25, "snippet": 16}
    file_hash = hashlib.file_digest(video.open("rb"), "sha256").hexdigest()
    key = digest({"video": file_hash, "preprocess": config})
    cache = ROOT / "data/features" / f"{key}.npy"
    sidecar = cache.with_suffix(".json")
    if cache.exists() and sidecar.exists():
        return Features.model_validate_json(sidecar.read_text())
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not cap.isOpened() or fps <= 0:
        raise ValueError(f"Cannot decode video: {video}")
    processor: Any = None
    model: Any = None
    if not sample:
        from transformers import CLIPModel, CLIPProcessor

        model = CLIPModel.from_pretrained(model_id).to(device).eval()
        processor = CLIPProcessor.from_pretrained(model_id)
    features: list[Any] = []
    snippet: list[Any] = []
    index = 0
    next_sample = 0.0
    previous: Any = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            time_s = index / fps
            index += 1
            # WHY: Time resampling keeps snippet duration independent of source FPS.
            while next_sample <= time_s + 1e-8:
                if sample:
                    small = cv2.resize(frame, (16, 8)).astype(np.float32) / 255
                    motion = 0.0 if previous is None else float(np.abs(small - previous).mean())
                    vector = np.concatenate((small.flatten(), np.array([motion], dtype=np.float32)))
                    previous = small
                else:
                    import torch
                    from PIL import Image

                    inputs = processor(
                        images=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), return_tensors="pt"
                    ).to(device)
                    with torch.inference_mode():
                        vector = model.get_image_features(**inputs).float().cpu().numpy()[0]
                snippet.append(vector)
                next_sample += 1 / 25
                if len(snippet) == 16:
                    features.append(np.mean(snippet, axis=0))
                    snippet = []
        if snippet:
            features.append(np.mean(snippet, axis=0))
    finally:
        cap.release()
    if not features:
        raise ValueError("Video contains no decodable frames")
    array = np.asarray(features, dtype=np.float32)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, array)
    output = Features(
        cache_path=cache.relative_to(ROOT).as_posix(),
        n_snippets=len(array),
        feature_dim=array.shape[1],
        extractor=str(config["model"]),
        cache_key=key,
        snippet_s=16 / 25,
    )
    write_json(sidecar, output.model_dump())
    return output
