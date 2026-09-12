import argparse
import json
from pathlib import Path

import cv2

from argus.api.store import Store
from argus.config import ROOT, device_name
from argus.orchestrator import run
from argus.schema import Source

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an offline research clip using a validated VLM cache")
    parser.add_argument("video", type=Path)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--severity-model", type=Path)
    parser.add_argument("--dataset", default="Local research")
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--blur-faces",
        action="store_true",
        help="Use full-frame blur for derived keyframes; raw input remains local",
    )
    args = parser.parse_args()
    video = args.video.resolve()
    if not video.is_relative_to(ROOT):
        parser.error("Place the clip inside the project data/raw folder first")
    cap = cv2.VideoCapture(str(video))
    fps, frames = cap.get(cv2.CAP_PROP_FPS), cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    if fps <= 0 or frames <= 0:
        parser.error("Cannot decode clip")
    source = Source(
        dataset=args.dataset,
        clip_id=video.stem,
        video_path=video.relative_to(ROOT).as_posix(),
        fps=fps,
        duration_s=frames / fps,
        sample=False,
        split="test",
    )
    record = run(
        source,
        args.claims,
        args.checkpoint,
        args.severity_model,
        device_name(args.device),
        blur_faces=args.blur_faces,
    )
    Store(ROOT / "data/argus.sqlite").put(record)
    print(json.dumps(record.model_dump(mode="json"), indent=2))
