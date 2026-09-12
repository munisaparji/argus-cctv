"""Remove uniform recorder padding while preserving the recorded screen content."""

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    source = ROOT / "deliverables/ARGUS_Demo_Walkthrough.webm"
    output = ROOT / "artifacts/qa/normalized-walkthrough.webm"
    (ROOT / "artifacts/qa/video-review").mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(source))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"VP80"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError("VP8 video writer unavailable")
    index = 0
    corrected = 0
    selected = {int(t * fps): t for t in [7, 22, 37, 52, 67, 82, 97, 112, 127, 142, 157, 172]}
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            # The Windows recorder can pad an initial smaller screen with RGB 128.
            if np.max(np.abs(frame[-8:, -8:].astype(float) - 128)) < 12:
                mask = np.max(np.abs(frame.astype(np.int16) - 128), axis=2) > 16
                ys, xs = np.where(mask)
                if len(xs) and xs.max() < width - 40 and ys.max() < height - 40:
                    frame = cv2.resize(frame[: ys.max() + 1, : xs.max() + 1], (width, height))
                    corrected += 1
            writer.write(frame)
            if index in selected:
                cv2.imwrite(str(ROOT / f"artifacts/qa/video-review/final-{selected[index]:03d}.jpg"), frame)
            index += 1
    finally:
        cap.release()
        writer.release()
    check = cv2.VideoCapture(str(output))
    assert int(check.get(cv2.CAP_PROP_FRAME_COUNT)) == index
    assert check.read()[0]
    check.release()
    output.replace(source)
    print(f"Validated {index} frames; removed recorder padding from {corrected} frames")


if __name__ == "__main__":
    main()
