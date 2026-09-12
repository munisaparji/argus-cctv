from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Protocol

import cv2
import numpy as np

from argus.schema import Detection, Evidence, Keyframe, Track


class ObjectDetector(Protocol):
    name: str

    def detect(self, frame: Any) -> list[tuple[str, float, tuple[float, float, float, float]]]: ...


class SyntheticDetector:
    """Actual pixel segmentation for authored coloured sprites, not real-world perception."""

    name = "synthetic-colour-segmentation-v1"

    def detect(self, frame: Any) -> list[tuple[str, float, tuple[float, float, float, float]]]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        result = []
        for label, low, high in [
            ("person", (75, 110, 100), (105, 255, 255)),
            ("bag", (15, 100, 100), (40, 255, 255)),
            ("car", (125, 70, 100), (160, 255, 255)),
        ]:
            mask = cv2.inRange(hsv, np.array(low), np.array(high))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                if cv2.contourArea(contour) < 50:
                    continue
                x, y, w, h = cv2.boundingRect(contour)
                result.append((label, 1.0, (float(x), float(y), float(w), float(h))))
        return result


class DetrDetector:
    name = "facebook/detr-resnet-50"

    def __init__(self, device: str = "cpu", threshold: float = 0.65) -> None:
        from transformers import AutoImageProcessor, AutoModelForObjectDetection

        self.device = device
        self.threshold = threshold
        processor_factory: Any = AutoImageProcessor
        self.processor: Any = processor_factory.from_pretrained(self.name)
        self.model = AutoModelForObjectDetection.from_pretrained(self.name).to(device).eval()

    def detect(self, frame: Any) -> list[tuple[str, float, tuple[float, float, float, float]]]:
        import torch
        from PIL import Image

        inputs = self.processor(
            images=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), return_tensors="pt"
        ).to(self.device)
        with torch.inference_mode():
            output = self.model(**inputs)
        sizes = torch.tensor([frame.shape[:2]], device=self.device)
        result = self.processor.post_process_object_detection(
            output, target_sizes=sizes, threshold=self.threshold
        )[0]
        detections = []
        for score, label, box in zip(result["scores"], result["labels"], result["boxes"], strict=False):
            x1, y1, x2, y2 = box.tolist()
            detections.append(
                (self.model.config.id2label[int(label)], float(score), (x1, y1, x2 - x1, y2 - y1))
            )
        return detections


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    intersection = max(0, min(ax + aw, bx + bw) - max(ax, bx)) * max(0, min(ay + ah, by + bh) - max(ay, by))
    return intersection / max(1e-9, aw * ah + bw * bh - intersection)


class IoUTracker:
    def __init__(self) -> None:
        self.active: dict[int, tuple[str, tuple[float, float, float, float], float]] = {}
        self.next_id = 1

    def update(
        self, rows: list[tuple[str, float, tuple[float, float, float, float]]], time_s: float
    ) -> list[int]:
        self.active = {k: v for k, v in self.active.items() if time_s - v[2] <= 2}
        used: set[int] = set()
        output = []
        for cls, _, box in rows:
            candidates = [
                (iou(box, old[1]), tid)
                for tid, old in self.active.items()
                if old[0] == cls and tid not in used
            ]
            best, tid = max(candidates, default=(0.0, -1))
            if best < 0.25:
                tid = self.next_id
                self.next_id += 1
            used.add(tid)
            self.active[tid] = (cls, box, time_s)
            output.append(tid)
        return output


def build_evidence(
    video: Path,
    start: float,
    end: float,
    output_dir: Path,
    root: Path,
    detector: ObjectDetector,
    blur_faces: bool = False,
) -> Evidence:
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        raise ValueError("Invalid video FPS")
    tracker = IoUTracker()
    objects: list[Detection] = []
    tracks: dict[int, Track] = {}
    counts: dict[str, int] = {}
    candidates: list[tuple[float, int, float, Any]] = []
    previous: Any = None
    try:
        for frame_id in range(int(start * fps), int(end * fps), max(1, round(fps / 5))):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ok, frame = cap.read()
            if not ok:
                continue
            time_s = frame_id / fps
            rows = detector.detect(frame)
            ids = tracker.update(rows, time_s)
            frame_counts = Counter(row[0] for row in rows)
            for cls, count in frame_counts.items():
                counts[cls] = max(counts.get(cls, 0), count)
            for (cls, conf, box), tid in zip(rows, ids, strict=False):
                objects.append(
                    Detection(
                        detection_id=f"d{len(objects)}",
                        cls=cls,
                        conf=conf,
                        frame=frame_id,
                        time_s=time_s,
                        bbox=box,
                        track_id=tid,
                    )
                )
                track = tracks.setdefault(tid, Track(track_id=tid, cls=cls, frames=[], trajectory=[]))
                track.frames.append(frame_id)
                track.trajectory.append((box[0] + box[2] / 2, box[1] + box[3] / 2))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            motion = 0 if previous is None else float(cv2.absdiff(gray, previous).mean())
            previous = gray
            if blur_faces:
                # WHY: Full-frame privacy rendering avoids promising a face detector will find every face.
                frame = cv2.GaussianBlur(frame, (51, 51), 0)
            candidates.append((len(rows) + motion / 10, frame_id, time_s, frame))
    finally:
        cap.release()
    output_dir.mkdir(parents=True, exist_ok=True)
    selected: list[Keyframe] = []
    for _, frame_id, time_s, frame in sorted(candidates, key=lambda row: row[0], reverse=True):
        if any(abs(time_s - k.time_s) < 0.5 for k in selected):
            continue
        path = output_dir / f"frame_{frame_id}.jpg"
        cv2.imwrite(str(path), frame)
        selected.append(
            Keyframe(
                frame=frame_id,
                time_s=time_s,
                path=path.relative_to(root).as_posix(),
                reason="detection_density_and_motion",
            )
        )
        if len(selected) == 4:
            break
    return Evidence(
        objects=objects,
        tracks=list(tracks.values()),
        counts=counts,
        keyframes=sorted(selected, key=lambda k: k.time_s),
        extractor=detector.name,
        limitations=[
            "Tracks are clip-local geometric associations, not identities.",
            "Missing detection is missing support, not proof of absence.",
            "No independent contact, damage, intent or role detector is enabled.",
        ],
    )
