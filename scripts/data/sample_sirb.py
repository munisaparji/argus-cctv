import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

from argus.config import write_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/sirb/assignments.json"))
    args = parser.parse_args()
    rng = random.Random(args.seed)
    groups = defaultdict(list)
    for row in pd.read_parquet(args.index).to_dict("records"):
        groups[(row["category"], row.get("expected_severity", "unknown"))].append(row)
    for group in groups.values():
        rng.shuffle(group)
    selected = []
    while len(selected) < args.count and any(groups.values()):
        for key in sorted(groups):
            if groups[key] and len(selected) < args.count:
                selected.append(groups[key].pop())
    overlap = set(rng.sample(range(len(selected)), round(len(selected) * 0.2)))
    for i, row in enumerate(selected):
        row["annotators"] = (
            ["annotator-a", "annotator-b"]
            if i in overlap
            else ["annotator-a" if i % 2 == 0 else "annotator-b"]
        )
        # WHY: Source-level split assignment must precede cutting adjacent windows from a source video.
        row["annotation_split"] = "test" if i % 5 == 0 else "val" if i % 5 == 1 else "train"
    write_json(
        args.output,
        {
            "seed": args.seed,
            "target": args.count,
            "actual": len(selected),
            "double_annotated": len(overlap),
            "assignments": selected,
        },
    )
    print(json.dumps({"selected": len(selected), "overlap": len(overlap)}))
