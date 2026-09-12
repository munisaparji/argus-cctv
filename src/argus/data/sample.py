from __future__ import annotations

import json

import cv2
import numpy as np

from argus.config import ROOT, write_json
from argus.schema import Source

SCENES = [
    ("sample_counter_01", 2, True, False),
    ("sample_corridor_02", 1, False, False),
    ("sample_bag_03", 2, True, False),
    ("sample_parking_04", 1, False, True),
    ("sample_group_05", 3, False, False),
    ("sample_quiet_06", 0, False, False),
    ("sample_entry_07", 2, False, False),
    ("sample_vehicle_08", 0, False, True),
]


def generate() -> list[Source]:
    folder = ROOT / "data/sample"
    folder.mkdir(parents=True, exist_ok=True)
    sources = []
    for name, people, bag, vehicle in SCENES:
        video = folder / f"{name}.mp4"
        fps, duration = 25, 6
        if not video.exists():
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (640, 360))
            if not writer.isOpened():
                raise RuntimeError("OpenCV MP4 encoder unavailable")
            for frame_id in range(fps * duration):
                frame = np.full((360, 640, 3), (24, 29, 35), np.uint8)
                for y in range(80, 360, 40):
                    cv2.line(frame, (0, y), (640, y), (37, 43, 49), 1)
                for x in range(0, 640, 80):
                    cv2.line(frame, (x, 80), (x, 360), (37, 43, 49), 1)
                cv2.rectangle(frame, (380, 110), (590, 155), (66, 72, 80), -1)
                cv2.putText(
                    frame,
                    "ARGUS / SYNTHETIC TEST SCENE",
                    (22, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (190, 200, 212),
                    1,
                )
                cv2.putText(
                    frame,
                    f"CAM 01   00:00:{frame_id / fps:05.2f}   SAMPLE",
                    (22, 337),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.43,
                    (170, 185, 195),
                    1,
                )
                for person in range(people):
                    x = 80 + person * 145 + int(min(frame_id, 90) * 0.7)
                    y = 165 + person * 25
                    cv2.circle(frame, (x + 15, y), 12, (225, 210, 35), -1)
                    cv2.rectangle(frame, (x + 3, y + 10), (x + 27, y + 62), (225, 210, 35), -1)
                    cv2.line(frame, (x + 8, y + 60), (x + 3, y + 83), (225, 210, 35), 6)
                    cv2.line(frame, (x + 23, y + 60), (x + 28, y + 83), (225, 210, 35), 6)
                if bag:
                    cv2.rectangle(frame, (333, 231), (365, 258), (45, 185, 240), -1)
                if vehicle:
                    x = 340 - int(frame_id * 0.6)
                    cv2.rectangle(frame, (x, 265), (x + 90, 302), (210, 70, 195), -1)
                writer.write(frame)
                if frame_id == 50:
                    cv2.imwrite(str(folder / f"{name}.jpg"), frame)
            writer.release()
        preview = video.with_suffix(".webm")
        if not preview.exists():
            capture = cv2.VideoCapture(str(video))
            browser_writer = cv2.VideoWriter(str(preview), cv2.VideoWriter_fourcc(*"VP80"), fps, (640, 360))
            if not browser_writer.isOpened():
                raise RuntimeError("WebM encoder unavailable")
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                browser_writer.write(frame)
            capture.release()
            browser_writer.release()
        source = Source(
            dataset="Synthetic sample",
            clip_id=name,
            video_path=video.relative_to(ROOT).as_posix(),
            fps=fps,
            duration_s=duration,
            sample=True,
        )
        sources.append(source)
        claims = []
        if people:
            claims.append(
                {
                    "claim_id": "c1",
                    "text": f"{people} people are visible in the scene.",
                    "type": "OBSERVATION",
                    "entities": ["person"],
                    "time_span_s": [1.28, 2.56],
                    "self_confidence": 0.9,
                    "predicate": "count",
                    "counts": {"person": people},
                }
            )
        if bag:
            claims.append(
                {
                    "claim_id": "c2",
                    "text": "A bag is visible.",
                    "type": "OBSERVATION",
                    "entities": ["bag"],
                    "time_span_s": [1.28, 2.56],
                    "self_confidence": 0.8,
                    "predicate": "presence",
                }
            )
        if vehicle:
            claims.append(
                {
                    "claim_id": "c3",
                    "text": "A car is visible.",
                    "type": "OBSERVATION",
                    "entities": ["car"],
                    "time_span_s": [1.28, 2.56],
                    "self_confidence": 0.9,
                    "predicate": "presence",
                }
            )
        if name in {"sample_counter_01", "sample_bag_03"}:
            claims.append(
                {
                    "claim_id": "c4",
                    "text": "A person is holding a knife.",
                    "type": "OBSERVATION",
                    "entities": ["person", "knife"],
                    "time_span_s": [1.28, 2.56],
                    "self_confidence": 0.94,
                    "predicate": "presence",
                }
            )
            claims.append(
                {
                    "claim_id": "c5",
                    "text": "The person may intend to take the bag.",
                    "type": "OBSERVATION",
                    "entities": ["person", "bag"],
                    "time_span_s": [1.28, 2.56],
                    "self_confidence": 0.7,
                    "predicate": "intent",
                }
            )
        if not claims:
            claims.append(
                {
                    "claim_id": "c1",
                    "text": "The scene does not provide enough evidence to describe an event.",
                    "type": "UNCERTAINTY",
                    "entities": [],
                    "time_span_s": [0, 6],
                    "self_confidence": 0.3,
                    "predicate": "unknown",
                }
            )
        cache = folder / f"{name}.claims.json"
        if not cache.exists():
            write_json(cache, {"claims": claims})
    write_json(folder / "sources.json", [source.model_dump() for source in sources])
    (folder / "README.md").write_text(
        "# Synthetic sample\n\nEight procedurally generated scenes. No human subjects or third-party footage. Features and evidence are computed from pixels. Claims are authored fixtures with deliberate errors. Labels are software fixtures, not human SIRB annotations. Project-authored sample assets are CC0-1.0.\n",
        encoding="utf-8",
    )
    return sources


def load_sources() -> list[Source]:
    path = ROOT / "data/sample/sources.json"
    return (
        [Source.model_validate(row) for row in json.loads(path.read_text())] if path.exists() else generate()
    )
