import argparse
import json
from pathlib import Path

from argus.config import device_name
from argus.modules.m1_preprocess import extract

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    print(
        json.dumps(
            extract(args.video, args.sample, "cpu" if args.sample else device_name(args.device)).model_dump(),
            indent=2,
        )
    )
